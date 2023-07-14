---
title: Setup workspace
about: Setup your code workspace
contributors: VYT <https://github.com/vytdev>
---

If you want to contribute or make your own add-on plugins, you are in the right place!
Here you will know the basic requirements before you get started working with this add-on.

## Requirements

To be able to do your changes, you need the following:

- Experience in programming
- Knows the basics of [TypeScript](https://www.typescriptlang.org/)
- [Git](https://git-scm.org/)
- [Python 3](https://python.org/)
- [NodeJS](https://nodejs.org/) (we prefer the LTS or long-term support version)
- An editor, like VSCode in Windows

If you haven't a Desktop, don't worry. You can still make your changes using your
mobile device, but also you need the following:

- Termux (search on F-Droid) or any other CLI emulator that supports linux environment
- ZArchiver in Android or Documents in iOS, for handling built packages
- An editor like Acode (available on Google Play)

After installing these mobile apps, you have to setup these also. Open Termux (or other),
then run:

```bash
pkg update; pkg upgrade # update packages

# install git
pkg install git

# installing python
pkg install python3 python-pip

# installing nodejs
pkg install nodejs-lts # recommended version of nodejs
```

After you got these requirements, you'll need to install the projects dependencies:

```bash
# installing python dependencies
python3 -m pip install -r "requirements.txt" # or,
py -m pip install -r "requirements.txt"

# installing nodejs dependencies
npm i # or,
yarn install
```

*Copy the scripts above and paste it in the terminal/CLI.*

Once you've done, you can start doing your changes to the code!

## Automating

You'll need to debug the project once you've done with your changes (or while doing
your changes) so your code will never get errors.

### Python script

There's a script I added to the root of project's source code. You can use it to have
test your changes directly to Minecraft without getting rid to delete and re-import
the add-on everytime, or to do simple tasks on your workspace and the add-on like
cleaning-up, re-building, and packing `.mcaddon` files. Here is how to use the script:

| Parameter       | Description                                                                                     |
| :-------------: | :---------------------------------------------------------------------------------------------- |
| `--sync`, `-s`  | Synchronize the built add-on to Minecraft.                                                      |
| `--build`, `-b` | Override build the add-on.                                                                      |
| `--debug`, `-d` | Build the add-on in debug mode (this may spam your logs).                                       |
| `--clean`, `-c` | Cleanup your workspace, removes last builds, distribution files, source maps, and other caches. |
| `--watch`, `-w` | Build the add-on as you make changes to it.                                                     |
| `--pack`, `-p`  | Packages the add-on into a `.mcpack` archive.                                                   |

You can also get this message on your terminal by running `python3 tool.py -h`.

### NPM

Run `npm run PARAM` to use, replace PARAM to any parameters below.

| Parameter  | Description                                                                                                                                   |
| :--------: | :-------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs`     | Build these docs, you need to clone also the docs repo (`https://github.com/vytdev/vytdev.github.io`) on folder where this project cloned to. |
| `test`     | Test the code, same as `npm test`                                                                                                             |
| `debug`    | Debug the code, shortcut for `python3 tool.py -cbds`                                                                                          |
| `build`    | Build scripts and the add-on, shortcut for `python3 tool.py -cb`                                                                              |
| `sync`     | Re-sync add-on to Minecraft (once), shortcut for `python3 tool.py -s`                                                                         |
| `lint`     | Runs `eslint` to check scripts                                                                                                                |
| `lint-fix` | Runs `eslint` and fix some fixable errors                                                                                                     |
