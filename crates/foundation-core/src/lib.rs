//! Executable reference semantics for `scalar-wrapping-v1` expressions.
//! Evaluation is not proof checking or authorization to execute generated code.

#![forbid(unsafe_code)]

use std::collections::BTreeMap;

pub const SCALAR_PROFILE: &str = "scalar-wrapping-v1";
/// Operational cutoffs, not bounds on the semantic i64 input domain.
pub const MAX_EXPRESSION_DEPTH: usize = 64;
pub const MAX_EXPRESSION_NODES: usize = 4096;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Type {
    I64,
    Bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Value {
    I64(i64),
    Bool(bool),
}

impl Value {
    pub fn value_type(self) -> Type {
        match self {
            Self::I64(_) => Type::I64,
            Self::Bool(_) => Type::Bool,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BinaryOp {
    AddWrap,
    SubWrap,
    MulWrap,
    DivWrap,
    Eq,
    LtSigned,
    LeSigned,
    GtSigned,
    GeSigned,
    And,
    Or,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Expr {
    Int(i64),
    Bool(bool),
    Var(String),
    Binary {
        op: BinaryOp,
        left: Box<Expr>,
        right: Box<Expr>,
    },
    If {
        condition: Box<Expr>,
        then_branch: Box<Expr>,
        else_branch: Box<Expr>,
    },
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Parameter {
    pub name: String,
    pub value_type: Type,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Program {
    pub semantic_profile_id: String,
    pub parameters: Vec<Parameter>,
    pub return_type: Type,
    pub body: Expr,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ScalarError {
    UnsupportedProfile(String),
    DuplicateParameter(String),
    UnboundVariable(String),
    TypeMismatch { expected: Type, actual: Type },
    ArgumentCount { expected: usize, actual: usize },
    ResourceLimit,
    DivideByZero,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum LiteralError {
    NonCanonical,
    OutOfRange,
}

/// Parse the schema's decimal string form without a JSON-number/float roundtrip.
pub fn parse_i64_decimal(text: &str) -> Result<i64, LiteralError> {
    let digits = text.strip_prefix('-').unwrap_or(text);
    if text != "0"
        && (digits.is_empty()
            || digits.starts_with('0')
            || !digits.bytes().all(|b| b.is_ascii_digit()))
    {
        return Err(LiteralError::NonCanonical);
    }
    text.parse().map_err(|_| LiteralError::OutOfRange)
}

fn same_type(expected: Type, actual: Type) -> Result<(), ScalarError> {
    if expected == actual {
        Ok(())
    } else {
        Err(ScalarError::TypeMismatch { expected, actual })
    }
}

fn binary_type(op: BinaryOp, left: Type, right: Type) -> Result<Type, ScalarError> {
    same_type(left, right)?;
    match op {
        BinaryOp::Eq => Ok(Type::Bool),
        BinaryOp::And | BinaryOp::Or => {
            same_type(Type::Bool, left)?;
            Ok(Type::Bool)
        }
        BinaryOp::LtSigned | BinaryOp::LeSigned | BinaryOp::GtSigned | BinaryOp::GeSigned => {
            same_type(Type::I64, left)?;
            Ok(Type::Bool)
        }
        _ => {
            same_type(Type::I64, left)?;
            Ok(Type::I64)
        }
    }
}

/// Apply an operator to already evaluated values. Short circuiting lives in
/// `Program::evaluate`, where the right expression can remain unevaluated.
pub fn apply(op: BinaryOp, left: Value, right: Value) -> Result<Value, ScalarError> {
    binary_type(op, left.value_type(), right.value_type())?;
    match (op, left, right) {
        (BinaryOp::Eq, a, b) => Ok(Value::Bool(a == b)),
        (BinaryOp::And, Value::Bool(a), Value::Bool(b)) => Ok(Value::Bool(a && b)),
        (BinaryOp::Or, Value::Bool(a), Value::Bool(b)) => Ok(Value::Bool(a || b)),
        (op, Value::I64(a), Value::I64(b)) => match op {
            BinaryOp::AddWrap => Ok(Value::I64(a.wrapping_add(b))),
            BinaryOp::SubWrap => Ok(Value::I64(a.wrapping_sub(b))),
            BinaryOp::MulWrap => Ok(Value::I64(a.wrapping_mul(b))),
            BinaryOp::DivWrap if b == 0 => Err(ScalarError::DivideByZero),
            BinaryOp::DivWrap => Ok(Value::I64(a.wrapping_div(b))),
            BinaryOp::LtSigned => Ok(Value::Bool(a < b)),
            BinaryOp::LeSigned => Ok(Value::Bool(a <= b)),
            BinaryOp::GtSigned => Ok(Value::Bool(a > b)),
            BinaryOp::GeSigned => Ok(Value::Bool(a >= b)),
            _ => Err(ScalarError::TypeMismatch {
                expected: Type::Bool,
                actual: Type::I64,
            }),
        },
        _ => Err(ScalarError::TypeMismatch {
            expected: Type::I64,
            actual: Type::Bool,
        }),
    }
}

impl Program {
    /// Check every branch before evaluation, including unreachable branches.
    pub fn validate(&self) -> Result<(), ScalarError> {
        if self.semantic_profile_id != SCALAR_PROFILE {
            return Err(ScalarError::UnsupportedProfile(
                self.semantic_profile_id.clone(),
            ));
        }
        let mut parameters = BTreeMap::new();
        for parameter in &self.parameters {
            if parameters
                .insert(parameter.name.as_str(), parameter.value_type)
                .is_some()
            {
                return Err(ScalarError::DuplicateParameter(parameter.name.clone()));
            }
        }
        let result = infer(&self.body, &parameters, 1, &mut 0)?;
        same_type(self.return_type, result)
    }

    /// Evaluate a pure scalar expression. A successful return is a concrete
    /// observation, not an equivalence certificate or acceptance result.
    pub fn evaluate(&self, arguments: &[Value]) -> Result<Value, ScalarError> {
        self.validate()?;
        if arguments.len() != self.parameters.len() {
            return Err(ScalarError::ArgumentCount {
                expected: self.parameters.len(),
                actual: arguments.len(),
            });
        }
        let mut environment = BTreeMap::new();
        for (parameter, argument) in self.parameters.iter().zip(arguments) {
            same_type(parameter.value_type, argument.value_type())?;
            environment.insert(parameter.name.as_str(), *argument);
        }
        evaluate(&self.body, &environment)
    }
}

fn infer(
    expr: &Expr,
    parameters: &BTreeMap<&str, Type>,
    depth: usize,
    nodes: &mut usize,
) -> Result<Type, ScalarError> {
    *nodes += 1;
    if depth > MAX_EXPRESSION_DEPTH || *nodes > MAX_EXPRESSION_NODES {
        return Err(ScalarError::ResourceLimit);
    }
    match expr {
        Expr::Int(_) => Ok(Type::I64),
        Expr::Bool(_) => Ok(Type::Bool),
        Expr::Var(name) => parameters
            .get(name.as_str())
            .copied()
            .ok_or_else(|| ScalarError::UnboundVariable(name.clone())),
        Expr::Binary { op, left, right } => {
            let left = infer(left, parameters, depth + 1, nodes)?;
            let right = infer(right, parameters, depth + 1, nodes)?;
            binary_type(*op, left, right)
        }
        Expr::If {
            condition,
            then_branch,
            else_branch,
        } => {
            same_type(Type::Bool, infer(condition, parameters, depth + 1, nodes)?)?;
            let then_type = infer(then_branch, parameters, depth + 1, nodes)?;
            same_type(then_type, infer(else_branch, parameters, depth + 1, nodes)?)?;
            Ok(then_type)
        }
    }
}

fn evaluate(expr: &Expr, environment: &BTreeMap<&str, Value>) -> Result<Value, ScalarError> {
    match expr {
        Expr::Int(value) => Ok(Value::I64(*value)),
        Expr::Bool(value) => Ok(Value::Bool(*value)),
        Expr::Var(name) => environment
            .get(name.as_str())
            .copied()
            .ok_or_else(|| ScalarError::UnboundVariable(name.clone())),
        Expr::Binary { op, left, right } => {
            let left = evaluate(left, environment)?;
            match (op, left) {
                (BinaryOp::And, Value::Bool(false)) => return Ok(Value::Bool(false)),
                (BinaryOp::Or, Value::Bool(true)) => return Ok(Value::Bool(true)),
                _ => {}
            }
            apply(*op, left, evaluate(right, environment)?)
        }
        Expr::If {
            condition,
            then_branch,
            else_branch,
        } => match evaluate(condition, environment)? {
            Value::Bool(true) => evaluate(then_branch, environment),
            Value::Bool(false) => evaluate(else_branch, environment),
            value => Err(ScalarError::TypeMismatch {
                expected: Type::Bool,
                actual: value.value_type(),
            }),
        },
    }
}
