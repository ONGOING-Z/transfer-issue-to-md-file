# Transfer Issue to Markdown File

A Github action transfers issue with 'blog' and 'need_published' labels content to markdown file. After that, this action will create a pull
request to your current branch. And you can merge it manually.

In this action, I use this action - [create pull request][1] to make PR.

Note: only issues which have 'blog' and 'need_published' labels will be auto processed.

## Usage

example
```yml
name: CI
on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Example Action
        uses: ONGOING-Z/transfer-issue-to-md-file@v1.0.4
        with:
          my-token: ${{ secrets.MY_TOKEN }}
          path: "."
```

## Action inputs
| Name     | Description                                             | Default  |
|----------|---------------------------------------------------------|----------|
| my-token | the token that can access your repository               |          |
| path     | directory you want to save the generated markdown files | ./issues |

All inputs are **required**.

## Action Outputs
None

## License

[MIT][license_addr]


[1]: https://github.com/peter-evans/create-pull-request
[license_addr]: https://github.com/ONGOING-Z/transfer-issue-to-md-file/blob/main/LICENSE
