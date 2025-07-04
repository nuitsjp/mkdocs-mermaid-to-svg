# Boost Coverage

You are an excellent test engineer. To improve the test coverage of the following code, identify missing parts and add test cases as needed.

Since you are adding tests to code that should already work correctly, you do not need to follow the t-wada style TDD process.

## Target for Analysis

make test-cov

## Workflow

1. make test-cov
2. Confirmation of target coverage rate
3. git checkout -b boost-coverage-yyyyMMddHHmm
4. git push -u origin boost-coverage-yyyyMMddHHmm
5. make test-cov
6. Plan coverage improvement
7. Boost Coverage 1
    1. Add one test method
    2. make test-cov
    3. Fix test if needed
    4. make check-all
    5. Fix code quality issues
    6. make test-cov
    7. Fix test and update coverage plan if needed
8. Boost Coverage 2
    1. Add one test method
    2. make test-cov
    3. Fix test if needed
    4. make check-all
    5. Fix code quality issues
    6. make test-cov
    7. Fix test and update coverage plan if needed
9. ...
10. Commit & push

## Commit Message

Check the following to review your changes:

```bash
git status && git diff && git log --oneline -10
```

- Check changes with git status and git diff
- Ensure no unnecessary files are included
- Ensure no sensitive information is included
- Determine the type of change (feature/fix/refactor/docs/test)

If there are no issues, create a commit message following the format below and commit your changes:

コメントは日本語で記述すること。

```txt
<変更の種類>: <変更内容の要約>

詳細な説明（必要に応じて）

🤖 Generated with [GitHub Copilot](https://docs.github.com/ja/copilot)
```

- Clearly describe the changes
- Explain why the changes were made (focus on why, not just what)
- 日本語で記述
