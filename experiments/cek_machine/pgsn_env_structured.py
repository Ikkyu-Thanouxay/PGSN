"""Experimental suspended-Term path for the Python GSN milestone.

Slots carry environments through existing immutable data constructors. Builtin
shape inspection never evaluates an application. Reduction is implemented here;
only the selected Builtins' predicates and primitive operations are reused.
"""
from __future__ import annotations

from attrs import frozen

from pgsn.pgsn_term import (
    Abs, App, Boolean, Constant, DefineClass, Div, Integer, List, Minus,
    OverwriteRecord, PGSNClass, PGSNObject, Plus, Record, String, Term, Times,
)
from pgsn.pgsn_term import Variable


STRUCTURES = (List, Record, PGSNClass, PGSNObject, DefineClass, OverwriteRecord)
PRIMITIVES = (Plus, Minus, Times, Div, DefineClass, OverwriteRecord)
ATOMS = (Integer, String, Boolean, Constant) + PRIMITIVES


@frozen
class _Slot(Term):
    """Internal syntax boundary; never handed to the reference evaluator."""
    term: Term
    env: tuple[Term, ...]

    def _unsupported(self, *args):
        raise TypeError("An internal environment slot escaped the prototype")

    _eval_or_none = _unsupported
    _shift_or_none = _unsupported
    _subst_or_none = _unsupported
    _free_variables = _unsupported
    _remove_name_with_context = _unsupported


def _children(term, visit):
    """Visit in the same order as the reference container traversals."""
    if isinstance(term, App):
        return term.evolve(t1=visit(term.t1), t2=visit(term.t2))
    if isinstance(term, List):
        return term.evolve(terms=tuple(visit(t) for t in term.terms))
    if isinstance(term, Record):
        return term.evolve(attributes={k: visit(v) for k, v in term.attributes().items()})
    if isinstance(term, PGSNClass):
        inherit = visit(term.inherit) if term.inherit is not None else None
        return term.evolve(
            inherit=inherit,
            defaults={k: visit(v) for k, v in term.defaults().items()},
            methods={k: visit(v) for k, v in term.methods().items()},
        )
    if isinstance(term, PGSNObject):
        return term.evolve(
            instance=visit(term.instance),
            attributes={k: visit(v) for k, v in term.attributes().items()},
            methods={k: visit(v) for k, v in term.methods().items()},
        )
    return term


def needs_structured(term):
    if isinstance(term, STRUCTURES):
        return True
    if isinstance(term, App):
        return needs_structured(term.t1) or needs_structured(term.t2)
    if isinstance(term, Abs):
        return needs_structured(term.t)
    return False


def _slot(term, env):
    return _Slot.nameless(term=term, env=env)


def _expose(term):
    """Resolve bindings and expose syntax, without performing a reduction."""
    while isinstance(term, _Slot):
        source, env = term.term, term.env
        if isinstance(source, _Slot):
            term = source
        elif isinstance(source, Variable):
            if source.num is None or source.num >= len(env):
                raise TypeError("Free variable in structured environment evaluator")
            term = env[source.num]
        elif isinstance(source, Abs):
            return term
        else:
            term = _children(source, lambda child: _slot(child, env))
    return term


def _shape(term):
    exposed = _expose(term)
    # Applications and lambda bodies are opaque to all selected predicates.
    # Retaining the slot preserves their environment through primitive results.
    if isinstance(exposed, (App, _Slot)):
        return term if isinstance(term, _Slot) else _slot(term, ())
    return _children(exposed, _shape)


def _application(head, args):
    for arg in args:
        head = App.term(head, arg)
    return head


def _step(term):
    exposed = _expose(term)
    if isinstance(exposed, App):
        args = []
        head = exposed
        while isinstance(head, App):
            args.insert(0, head.t2)
            head = _expose(head.t1)
        if isinstance(head, _Slot) and isinstance(head.term, Abs):
            # Beta reduction extends the captured environment; no body rewrite.
            body = _slot(head.term.t, (args[0],) + head.env)
            return _application(body, args[1:])
        if isinstance(head, PRIMITIVES + (List, Record, PGSNClass, PGSNObject)):
            builtin, shaped_args = _shape(head), tuple(_shape(arg) for arg in args)
            if builtin.applicable_args(shaped_args):
                result, rest = builtin.apply_args(shaped_args)
                return _application(result, rest)
        reduced = _step(head)
        if reduced is not None:
            return _application(reduced, args)
        for i, arg in enumerate(args):
            reduced = _step(arg)
            if reduced is not None:
                return _application(head, args[:i] + [reduced] + args[i + 1:])
        return None  # Preserve stuck applications, as the reference does.
    if isinstance(exposed, (List, Record, PGSNClass, PGSNObject)):
        changed = False

        def advance(child):
            nonlocal changed
            reduced = _step(child)
            if reduced is None:
                return child
            changed = True
            return reduced

        result = _children(exposed, advance)
        return result if changed else None
    if isinstance(exposed, ATOMS):
        return None
    if isinstance(exposed, _Slot) and isinstance(exposed.term, Abs):
        # Escaping functions in structured data require normalization under
        # binders, outside this milestone. Never report them as evaluated data.
        raise TypeError("Escaping lambda in structured environment evaluator")
    raise TypeError(f"Unsupported term in structured environment evaluator: {type(exposed).__name__}")


def _materialize(term):
    exposed = _expose(term)
    if isinstance(exposed, _Slot):
        raise TypeError("Escaping lambda in structured environment evaluator")
    return _children(exposed, _materialize)


def eval_structured(term, env=()):
    if term.is_named:
        term = term.remove_name()
    runtime = _slot(term, tuple(_slot(arg.term, _environment(arg.env)) for arg in env))
    while True:
        reduced = _step(runtime)
        if reduced is None:
            return _materialize(runtime)
        runtime = reduced


def _environment(env):
    return tuple(_slot(arg.term, _environment(arg.env)) for arg in env)
