use foundation_core::{
    BinaryOp, Expr, LiteralError, MAX_EXPRESSION_DEPTH, Parameter, Program, SCALAR_PROFILE,
    ScalarError, Type, Value, apply, parse_i64_decimal,
};

fn binary(op: BinaryOp, left: Expr, right: Expr) -> Expr {
    Expr::Binary {
        op,
        left: Box::new(left),
        right: Box::new(right),
    }
}

fn program(body: Expr, return_type: Type) -> Program {
    Program {
        semantic_profile_id: SCALAR_PROFILE.into(),
        parameters: vec![],
        return_type,
        body,
    }
}

fn division_by_zero() -> Expr {
    binary(BinaryOp::DivWrap, Expr::Int(1), Expr::Int(0))
}

#[test]
fn overflow_is_the_same_machine_value_in_every_build_profile() {
    let cases = [
        (BinaryOp::AddWrap, i64::MAX, 1, i64::MIN),
        (BinaryOp::SubWrap, i64::MIN, 1, i64::MAX),
        (BinaryOp::MulWrap, i64::MAX, 2, -2),
        (BinaryOp::MulWrap, i64::MIN, -1, i64::MIN),
        (BinaryOp::AddWrap, i64::MIN, i64::MIN, 0),
    ];
    for (op, left, right, expected) in cases {
        assert_eq!(
            apply(op, Value::I64(left), Value::I64(right)),
            Ok(Value::I64(expected))
        );
    }
}

#[test]
fn division_truncates_toward_zero_and_preserves_minimum_overflow() {
    for (left, right, expected) in [
        (-7, 3, -2),
        (7, -3, -2),
        (-7, -3, 2),
        (i64::MIN, -1, i64::MIN),
        (i64::MIN, 1, i64::MIN),
    ] {
        assert_eq!(
            apply(BinaryOp::DivWrap, Value::I64(left), Value::I64(right)),
            Ok(Value::I64(expected))
        );
    }
    assert_eq!(
        apply(BinaryOp::DivWrap, Value::I64(i64::MIN), Value::I64(0)),
        Err(ScalarError::DivideByZero)
    );
}

#[test]
fn comparisons_use_signed_order() {
    for (op, left, right, expected) in [
        (BinaryOp::LtSigned, i64::MIN, 0, true),
        (BinaryOp::LeSigned, i64::MAX, i64::MAX, true),
        (BinaryOp::GtSigned, i64::MIN, i64::MAX, false),
        (BinaryOp::GeSigned, -1, 0, false),
        (BinaryOp::Eq, i64::MIN, i64::MIN, true),
    ] {
        assert_eq!(
            apply(op, Value::I64(left), Value::I64(right)),
            Ok(Value::Bool(expected))
        );
    }
    assert_eq!(
        apply(BinaryOp::Eq, Value::Bool(true), Value::Bool(false)),
        Ok(Value::Bool(false))
    );
}

#[test]
fn canonical_decimal_literals_keep_all_64_bits() {
    for (text, expected) in [
        ("-9223372036854775808", i64::MIN),
        ("9223372036854775807", i64::MAX),
        ("9007199254740993", 9_007_199_254_740_993),
        ("0", 0),
        ("-1", -1),
    ] {
        assert_eq!(parse_i64_decimal(text), Ok(expected));
    }
    for text in ["9223372036854775808", "-9223372036854775809"] {
        assert_eq!(parse_i64_decimal(text), Err(LiteralError::OutOfRange));
    }
    for text in [
        "", "+1", "01", "-0", "-01", "1.0", "1e3", " 1", "1 ", "１２", "-",
    ] {
        assert_eq!(parse_i64_decimal(text), Err(LiteralError::NonCanonical));
    }
}

#[test]
fn nonnegative_matches_the_independent_oracle_boundaries() {
    let mut p = program(
        Expr::If {
            condition: Box::new(binary(
                BinaryOp::GeSigned,
                Expr::Var("x".into()),
                Expr::Int(0),
            )),
            then_branch: Box::new(Expr::Var("x".into())),
            else_branch: Box::new(Expr::Int(0)),
        },
        Type::I64,
    );
    p.parameters.push(Parameter {
        name: "x".into(),
        value_type: Type::I64,
    });
    for (input, expected) in [(i64::MIN, 0), (-1, 0), (0, 0), (1, 1), (i64::MAX, i64::MAX)] {
        assert_eq!(p.evaluate(&[Value::I64(input)]), Ok(Value::I64(expected)));
    }
}

#[test]
fn unselected_branch_does_not_raise_an_error() {
    for condition in [true, false] {
        let (then_branch, else_branch) = if condition {
            (Expr::Int(42), division_by_zero())
        } else {
            (division_by_zero(), Expr::Int(42))
        };
        let p = program(
            Expr::If {
                condition: Box::new(Expr::Bool(condition)),
                then_branch: Box::new(then_branch),
                else_branch: Box::new(else_branch),
            },
            Type::I64,
        );
        assert_eq!(p.evaluate(&[]), Ok(Value::I64(42)));
    }
}

#[test]
fn boolean_short_circuit_preserves_error_observations() {
    for (op, left, expected) in [(BinaryOp::And, false, false), (BinaryOp::Or, true, true)] {
        let bad = binary(BinaryOp::Eq, division_by_zero(), Expr::Int(0));
        assert_eq!(
            program(binary(op, Expr::Bool(left), bad), Type::Bool).evaluate(&[]),
            Ok(Value::Bool(expected))
        );
    }
    for (op, left) in [(BinaryOp::And, true), (BinaryOp::Or, false)] {
        let bad = binary(BinaryOp::Eq, division_by_zero(), Expr::Int(0));
        assert_eq!(
            program(binary(op, Expr::Bool(left), bad), Type::Bool).evaluate(&[]),
            Err(ScalarError::DivideByZero)
        );
    }
}

#[test]
fn malformed_unreachable_code_is_rejected_before_execution() {
    let p = program(
        Expr::If {
            condition: Box::new(Expr::Bool(true)),
            then_branch: Box::new(Expr::Int(42)),
            else_branch: Box::new(Expr::Var("missing".into())),
        },
        Type::I64,
    );
    assert_eq!(
        p.evaluate(&[]),
        Err(ScalarError::UnboundVariable("missing".into()))
    );
    let p = program(
        binary(BinaryOp::And, Expr::Bool(false), Expr::Int(0)),
        Type::Bool,
    );
    assert!(matches!(
        p.evaluate(&[]),
        Err(ScalarError::TypeMismatch { .. })
    ));
}

#[test]
fn mixed_types_never_coerce() {
    for op in [
        BinaryOp::AddWrap,
        BinaryOp::Eq,
        BinaryOp::GeSigned,
        BinaryOp::And,
    ] {
        assert!(matches!(
            apply(op, Value::I64(1), Value::Bool(true)),
            Err(ScalarError::TypeMismatch { .. })
        ));
    }
    let p = program(Expr::Int(1), Type::Bool);
    assert!(matches!(
        p.validate(),
        Err(ScalarError::TypeMismatch { .. })
    ));
    let p = program(
        Expr::If {
            condition: Box::new(Expr::Int(1)),
            then_branch: Box::new(Expr::Int(2)),
            else_branch: Box::new(Expr::Int(3)),
        },
        Type::I64,
    );
    assert!(matches!(
        p.validate(),
        Err(ScalarError::TypeMismatch { .. })
    ));
    let p = program(
        Expr::If {
            condition: Box::new(Expr::Bool(true)),
            then_branch: Box::new(Expr::Int(2)),
            else_branch: Box::new(Expr::Bool(false)),
        },
        Type::I64,
    );
    assert!(matches!(
        p.validate(),
        Err(ScalarError::TypeMismatch { .. })
    ));
}

#[test]
fn parameters_are_unique_and_arguments_are_checked() {
    let mut p = program(Expr::Var("x".into()), Type::I64);
    p.parameters.push(Parameter {
        name: "x".into(),
        value_type: Type::I64,
    });
    assert_eq!(
        p.evaluate(&[]),
        Err(ScalarError::ArgumentCount {
            expected: 1,
            actual: 0
        })
    );
    assert_eq!(
        p.evaluate(&[Value::I64(1), Value::I64(2)]),
        Err(ScalarError::ArgumentCount {
            expected: 1,
            actual: 2
        })
    );
    assert!(matches!(
        p.evaluate(&[Value::Bool(true)]),
        Err(ScalarError::TypeMismatch { .. })
    ));
    p.parameters.push(Parameter {
        name: "x".into(),
        value_type: Type::Bool,
    });
    assert_eq!(
        p.validate(),
        Err(ScalarError::DuplicateParameter("x".into()))
    );
}

#[test]
fn unknown_profile_is_explicitly_unsupported() {
    let mut p = program(Expr::Int(0), Type::I64);
    p.semantic_profile_id = "mathematical-int-v1".into();
    assert_eq!(
        p.evaluate(&[]),
        Err(ScalarError::UnsupportedProfile(
            "mathematical-int-v1".into()
        ))
    );
}

#[test]
fn expression_resource_cutoff_is_an_error_not_a_semantic_value() {
    let mut body = Expr::Int(0);
    for _ in 1..MAX_EXPRESSION_DEPTH {
        body = binary(BinaryOp::AddWrap, body, Expr::Int(0));
    }
    assert_eq!(
        program(body.clone(), Type::I64).evaluate(&[]),
        Ok(Value::I64(0))
    );
    body = binary(BinaryOp::AddWrap, body, Expr::Int(0));
    assert_eq!(
        program(body, Type::I64).evaluate(&[]),
        Err(ScalarError::ResourceLimit)
    );
}

#[test]
fn wide_expression_trees_have_an_explicit_resource_outcome() {
    fn tree(levels: usize) -> Expr {
        if levels == 1 {
            Expr::Int(1)
        } else {
            binary(BinaryOp::AddWrap, tree(levels - 1), tree(levels - 1))
        }
    }
    // 4095 nodes are supported; 8191 nodes exceed the operational budget.
    assert_eq!(
        program(tree(12), Type::I64).evaluate(&[]),
        Ok(Value::I64(2048))
    );
    assert_eq!(
        program(tree(13), Type::I64).evaluate(&[]),
        Err(ScalarError::ResourceLimit)
    );
}

#[test]
fn boolean_parameters_and_operator_values_preserve_types() {
    let mut p = program(Expr::Var("flag".into()), Type::Bool);
    p.parameters.push(Parameter {
        name: "flag".into(),
        value_type: Type::Bool,
    });
    assert_eq!(p.evaluate(&[Value::Bool(false)]), Ok(Value::Bool(false)));
    for (op, left, right, expected) in [
        (BinaryOp::And, true, true, true),
        (BinaryOp::And, true, false, false),
        (BinaryOp::Or, false, true, true),
        (BinaryOp::Or, false, false, false),
        (BinaryOp::Eq, true, true, true),
    ] {
        assert_eq!(
            apply(op, Value::Bool(left), Value::Bool(right)),
            Ok(Value::Bool(expected))
        );
    }
}
