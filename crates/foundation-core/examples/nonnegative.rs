use foundation_core::{BinaryOp, Expr, Parameter, Program, SCALAR_PROFILE, Type, Value};

fn main() -> Result<(), foundation_core::ScalarError> {
    let program = Program {
        semantic_profile_id: SCALAR_PROFILE.into(),
        parameters: vec![Parameter {
            name: "x".into(),
            value_type: Type::I64,
        }],
        return_type: Type::I64,
        body: Expr::If {
            condition: Box::new(Expr::Binary {
                op: BinaryOp::GeSigned,
                left: Box::new(Expr::Var("x".into())),
                right: Box::new(Expr::Int(0)),
            }),
            then_branch: Box::new(Expr::Var("x".into())),
            else_branch: Box::new(Expr::Int(0)),
        },
    };
    println!("Reference evaluation only; no formal proof or translation check.");
    for input in [i64::MIN, -1, 0, 1, i64::MAX] {
        println!("{input} -> {:?}", program.evaluate(&[Value::I64(input)])?);
    }
    Ok(())
}
