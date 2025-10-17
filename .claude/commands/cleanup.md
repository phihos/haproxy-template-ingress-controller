Please analyze the diff between the current branch (including uncommitted changes) and the main branch and find opportunities for code cleanup.
That means unused code that can be deleted, useless comments, overcomplicated code that can be simplified, duplicate code that can be merged and any other measures that improve code quality.
Please disregard any kind of backward compatibility. We want zero technical debt.
If the diff contains any tests please do a cleanup there, too.
Check all conftest modules and reuse and consolidate as much test code (e.g. fixtures and factories) as possible.
Also check the filenames of all test modules if they are consistent and easy to attribute to production code. 
