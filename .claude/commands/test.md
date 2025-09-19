Run all tests, type checkers and linters and fix all outstanding issues. Do not ignore issues that have not been caused by the current code changes. ALl tests must pass.
Run the unit tests first and after all failures have been fixed run the full test suite.
Also ensure that each module has a test coverage of at least 90%.
When adding or modifying tests please check the corresponding conftest modules for existing fixtures and deep it as DRY as possible.
After everything is fixed please re-run all tests, type checkers and linters one last time to make sure.
Always run with pytest with "-n auto" for speed.