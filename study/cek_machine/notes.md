
###Normal lambda evaluator:
Function call means substitute the argument into the body.

###CEK evaluator:
Function call means store the argument in an environment, then evaluate the body.

###For example:

```((λx. λy. x) "A") "B"```

###Normal substitution:
```
((λx. λy. x) "A") "B"
→ (λy. "A") "B"
→ "A"
```

###CEK idea:
```
Apply λx to "A"
Environment: x = "A"

Result is λy. x with saved environment.

Apply λy to "B"
Environment: y = "B", x = "A"

Evaluate x
Look up x in environment
Result: "A"
```
