"""The real agent core.

Everything under ``backend.core`` is the working agent: an LLM-driven
tool-use loop over real files and a real shell, gated by user permission.
It is deliberately self-contained and does not depend on the older
simulation modules elsewhere in the tree.
"""
