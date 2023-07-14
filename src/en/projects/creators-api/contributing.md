---
title: Contribute to Creators’ API
about: An article about the contribution guide of the Creators’ API project
contributors: VYT <https://github.com/vytdev>
---

Thanks for contributing!

## Preparations

If you want to contribute, you need to do the following:

1. Create GitHub Account (you can skip this step if you already have one)
2. Go to the [project repository](https://github.com/vytdev/creators-api) then click Fork
3. Open your CLI, then run `git clone https://github.com/<your_username>/creators-api.git`
  and `cd creators-api`
4. Checkout your feature branch (`git checkout -b contributions/my-contributions`)
5. Install the project's dependencies (see [here](./setup.html#requirements))
6. Do your changes...
7. Test/debug your changes to the game (`python3 tool.py --build --watch --sync --debug`),
  and validate the code (`npm run lint`)
8. Commit your changes (`git add . && git commit -m "my contributions"`)
9. Push to the GitHub repo you've cloned (`git push`)
10. Open pull request

!!! note
    
    To be able to start a pull request, you need to make sure that your code passed the
    checks to the source. You can debug it without doing many commits by running `tsc` and
    `npm run lint`.
