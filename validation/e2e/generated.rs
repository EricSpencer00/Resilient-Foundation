#![forbid(unsafe_code)]

use foundation_core::{BinaryOp, Expr, Parameter, Program, Type, Value, parse_i64_decimal};

fn model() -> Program {
/* FOUNDATION_MODEL_BEGIN */
Program{semantic_profile_id:"scalar-wrapping-v1".into(),parameters:vec![Parameter{name:"x".into(),value_type:Type::I64}],return_type:Type::I64,body:Expr::If{condition:Box::new(Expr::Binary{op:BinaryOp::GeSigned,left:Box::new(Expr::Var("x".into())),right:Box::new(Expr::Int(0i64))}),then_branch:Box::new(Expr::Var("x".into())),else_branch:Box::new(Expr::Int(0i64))}}
/* FOUNDATION_MODEL_END */
}

fn invalid_input() -> ! {
    println!("{{\"kind\":\"invalid\",\"error\":\"InvalidInput\"}}");
    std::process::exit(1);
}

fn main() {
    let model = model();
    let text: Vec<String> = std::env::args().skip(1).collect();
    if text.len() != model.parameters.len() {
        invalid_input();
    }
    let mut arguments = Vec::new();
    for (parameter, value) in model.parameters.iter().zip(&text) {
        let argument = match parameter.value_type {
            Type::I64 => match parse_i64_decimal(value) {
                Ok(number) => Value::I64(number),
                Err(_) => invalid_input(),
            },
            Type::Bool => match value.as_str() {
                "true" => Value::Bool(true),
                "false" => Value::Bool(false),
                _ => invalid_input(),
            },
        };
        arguments.push(argument);
    }
    match model.evaluate(&arguments) {
        Ok(Value::I64(value)) => println!("{{\"kind\":\"return\",\"type\":\"i64\",\"value\":\"{value}\"}}"),
        Ok(Value::Bool(value)) => println!("{{\"kind\":\"return\",\"type\":\"bool\",\"value\":{value}}}"),
        Err(foundation_core::ScalarError::DivideByZero) => println!("{{\"kind\":\"error\",\"error\":\"DivideByZero\"}}"),
        Err(_) => invalid_input(),
    }
}
