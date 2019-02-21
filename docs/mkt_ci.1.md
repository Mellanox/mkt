---
date: 2018-6-1
footer: MKT
header: "Mellanox Kernel Tools"
layout: page
license: 'SPDX: Linux-OpenIB'
section: 1
title: mkt ci
---

# NAME

```sh
mkt ci [options] [project]
```

# DESCRIPTION

Locally run continious integration tests over source code by forking it
to temporal directory to allow seamless work on the code during CI run.

**mkt ci** provides an ability to perform in fast and efficient way self
checks. In current form, it generates reports for kernel only, but other
projects will be added in the near future.

Checkpatch, sparse and build with extra warnings (W=1) are part of this
**mkt ci**.

# OPTIONS

*project*
:	Project to build, executed with omitted proejct will try to guess the current proejct.

*---no-checkpatch*
:	Skip checkpatch check

*---rev*
:	Specify git SHA-1 to check, by default the HEAD will be checked.

*---no-sparse*
:	Don't run sparse check.

*---no-ignore-gerrit*
:	Print error in case Gerrit junk exists in patch, this option is usefull for submitters
    to external mailing lists, who are required to rmeove all internal metadata.

*---show-all*
:	Don't filter warnings/errors related to specific patch in test. This option is handy
    for everyone who wants to fix all warnings/errors.

*---no-extra-warnings*
:	Don't run W=1 check.

*---no-smatch*
:	Don't run smatch check.

# TOOLS

## CHECKPATCH

**Checkpatch** is a perl script to verify that your code conforms to the Linux kernel
coding style. **Checkpatch** produces many warnings; some of them are useful, and others
are more noisy or taste-based.

You should avoid introducing any new checkpatch warnings about lines longer than 80 characters,
but don't select existing warnings of that type to fix and submit patches for. In general, just
picking a cutoff point and wrapping the line doesn't make for a good fix for these warnings;
the result is often less readable than the original.

The right fix is often to refactor or rewrite code to simplify it (for instance, factoring out functions,
or changing if (success) { more code } to if (error) return ...;), and that's significantly more complex
than other checkpatch cleanups.

Don't attempt to fix "memory barrier without comment" warnings; writing the necessary comment
typically requires detailed knowledge about exactly what the code is doing and what specific memory
ordering issue the barrier is protecting against.

## SPARSE

**Sparse**, the semantic parser, provides a compiler frontend capable of parsing most of ANSI C as well as
many GCC extensions, and a collection of sample compiler backends, including a static analyzer also called
**sparse**. Sparse provides a set of annotations designed to convey semantic information about types,
such as what address space pointers point to, or what locks a function acquires or releases.

## SMATCH

**Smatch** is a tool that has been built on top of sparse and adds exactly that support, and more.
This extra analysis makes it possible to detect such things as conditions that will always (or never)
be true, pointers that might be null, and locks that end up in different states depending on which path
is taken through the code. This can be very helpful for validating error paths and other rarely tested code.

## EXTRA WARNINGS

Code compilation with W=1 option to catch warnings that may be relevant and does not occur too often.

# MKT

Part of the **mkt(1)** suite
