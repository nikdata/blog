---
title: "Using AI to Debug a Stubborn Python Error"
date: 2026-06-20
description: "I spent 45 minutes staring at a traceback before giving in and asking for help. The prompt mattered more than I expected."
draft: true
---

I was working on a data pipeline that kept failing silently. The dataframe looked fine at every checkpoint, but the final output was missing about 30% of the rows. No errors, no warnings, just fewer rows than expected.

After 45 minutes of print statements and head-scratching, I decided to describe the problem to an LLM and see what it came up with.

## The First Prompt (Too Vague)

My first attempt was lazy. I basically said "help me figure out what's wrong":

<div class="prompt">

```
My pandas dataframe is losing rows somewhere in my pipeline. I read in a CSV with 10,000 rows but only end up with about 7,000 at the end. How do I fix this?
```

</div>

The response was predictable. It gave me generic advice about checking for NaN values, looking at merge operations, and verifying my filters. Technically correct, but useless for my specific problem.

## The Second Prompt (With Context)

I tried again, this time including the actual code and being specific about what I had already checked:

<div class="prompt">

```
I have a pandas pipeline that reads a CSV (10,000 rows), applies some transformations, and writes the result. The output has ~7,000 rows. I've verified:

- No explicit dropna() calls
- No filters that should remove rows
- The CSV has no malformed rows

Here's the relevant code:

df = pd.read_csv("input.csv")
df["date"] = pd.to_datetime(df["date_str"])
df = df.merge(lookup_df, on="category_id")

The lookup_df has 45 unique category_id values. The input has 52 unique values.

What's causing the row loss?
```

</div>

This time it nailed it immediately. The merge was doing an inner join by default, dropping every row whose `category_id` didn't exist in the lookup table. Seven missing categories, roughly 3,000 rows gone.

The fix was obvious once I saw it:

```python
df = df.merge(lookup_df, on="category_id", how="left")
```

## The Takeaway

The quality of the answer was entirely determined by the quality of the prompt. The first attempt gave the model nothing to work with. The second gave it the exact code, what I had already ruled out, and the key numbers that pointed to the problem.

I think about this every time I write a prompt now. If I am being vague, I am going to get a vague answer.
