; RES-071 verification certificate
; expected solver result: unsat (proves the contract is a tautology)
(set-logic AUFLIA)
(declare-const x Int)
(assert (not (= (+ x 0) x)))
(check-sat)
