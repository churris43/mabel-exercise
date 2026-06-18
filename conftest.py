def pytest_itemcollected(item):
    """Overrides the displayed test name with its docstring if available."""
    if item.obj.__doc__:
        # Clean up whitespace and take the first line of the docstring
        clean_doc = item.obj.__doc__.strip().split("\n")[0]
        item._nodeid = f"{item.fspath.basename}:: {clean_doc}"