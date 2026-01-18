@copilot There is a syntax error in `telis_recruitment/leads/views.py` in the `opt_in()` function (around lines 292-293).

The old German docstring text was not fully removed and is now invalid Python code:

```python
    if getattr(request, 'limited', False):
        return JsonResponse({
            'error': 'Too many requests. Please try again in a few minutes.'
        }, status=429)
    Erstellt einen neuen Lead mit Source: landing_page  # ❌ This line should be deleted
    """                                                   # ❌ This line should be deleted
    try:
```

Please fix this by removing the two invalid lines (the German text `Erstellt einen neuen Lead mit Source: landing_page` and the stray `"""`). The docstring above already contains the English translation.