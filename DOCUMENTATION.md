You can download documentations for your vector using repomix

here are some commands for popular languages and frameworks

Dart Lang
```shell
repomix --remote https://github.com/dart-lang/sdk --include "docs/**/*.md" --ignore "docs/gsoc/**" --style xml -o repomix-dartlang.xml
```

React
```shell
repomix --remote https://github.com/reactjs/react.dev --include "src/content/reference/**/*.md,src/content/learn/**/*.md" --style xml -o repomix-react.xml
```