"""Reusable, tested circuit blocks shared by every board in this repo.

A block is a SKiDL @subcircuit that takes nets and PartSpecs as arguments and documents
*why* each part and value is there (with the datasheet/spec reference). Boards compose
blocks; blocks never pick MPNs themselves.
"""
