---
title: app — API Reference
about: Reference to plugin API
contributors: VYT <https://github.com/vytdev>
---

Plugins are the fundamental part of this project. It makes it easy to handle
module and package loading, with CommonJS like loading support. But what for?
This is for my planned extensions to the project, such as an anti-hack, and
many more.

#### Functions

`function app.load(target: string): any`
:   Loads a module or plugin using dot annotation. Like shown below:
    
        :::typescript
        import * as creator from "./framework/index.js";
        
        let Thread;
        
        // get thread class
        Thread = creator.app.load("threading.Thread");
        
        // same with this 
        Thread = creator.threading.Thread;
        
    
    - `target` - The expression where to find the object
    
    Returns any object, or all the exports of a module.
    

#### Classes

`class app.Loader`
:   A class that wraps all modules and packages within a plugin/library
    
    `constructor(pack?: app.LibObject | app.ModuleFunct | app.Module)`
    :   Initialize a new instance of this class.
        
        - `pack` - The module or dict of modules used within the plugin
        
    `readonly modules: app.CompiledLib`
    :   The compiled modules for the loader
        
        *This property is read-only*
        
    `app: app.Plugin`
    :   The Plugin instance where this loader was created for
        
    `entry: string`
    :   The entry point of the plugin loader, "index" by default
        
    `create(path: string, mod: app.Module | app.ModuleFunct): string;`
    :   Creates a new module, overrides old module if already exists in path
        
        - `path` - The path of the module
        - `mod` - The module instance
        
        Returns the normalized path of the module.
        
    `start(): app.Exports`
    :   Starts this plugin/app/library, at the given entry point.
        
    `reset(): void`
    :   Resets all modules
        
        *This can throw errors*
        

`class app.Module`
:   A class used to handle a module (or simply a function)
    
    `constructor(loader: app.Loader, path: string, mod: app.ModuleFunct)`
    :   Initialize a new instance of this class
        
        - `loader` - The library loader where this module belongs
        - `path` - The path of the module
        - `mod` - The module function
        
    `readonly path: string`
    :   The path of this module
        
        *This property is read-only*
        
    `readonly filename: string`
    :   The filename of this module
        
        *This property is read-only*
        
    `readonly action: app.ModuleFunct`
    :   The action function, where module runs
        
        *This property is read-only*
        
    `exports: app.Exports`
    :   Exported values of the module. Empty object by default.
        
    `loaded: boolean`
    :   Whether the module is fully loaded.
        
    `ran: boolean`
    :   Whether the module was ran
        
    `children: app.Module[]`
    :   All modules requestes by a module using require
        
    `loader: app.Loader`
    :   The loader of the plugin where this module is associated to
        
    `start(): app.Exports`
    :   Starts a module. Returns `this.exports` when fully loaded
        
    `reset(): boolean`
    :   Resets this module, returns `true` if succed
        
        *This can throw errors*
        

`class app.Plugin`
:   A class that creates and handles a plugin instance
    
    `constructor(name: string, loader: app.Loader | app.Module | app.LibObject | app.ModuleFunct)`
    :   Initializes a new instance of this class
        
        - `name` - The name of the plugin
        - `loader` - The context of the plugin
        
    `readonly name: string`
    :   The name of this plugin, passed on constructor
        
        *This property is read-only*
        
    `readonly loader: app.Loader`
    :   A loader instance that handles module loading
        
        *This property is read-only*
        
    `readonly context: app.Context`
    :   Plugin context, passed to all the modules of plugin as the first argument
        
        *This property is read-only*
        
    `register(): this`
    :   Registers this plugin to the global registry. Overrides if exists.
        
        Returns the plugin itself.
        
    `entry(path: string): this`
    :   Sets the entry point of the plugin
        
        - `path` - The entry point
        
        Returns the plugin itself.
        
    `start(...intent: any): app.Exports`
    :   Runs the plugin with some custom intents.
        
        - `intent` - The intent to pass on the plugin context
        
        Returns the exported value of the plugin entry point.
        
    `reset(): void`
    :   Resets the whole plugin
        
        *This can throw errors*
        

`class app.Context`
:   Plugin context/API used for handling itself, passed to each module within the
    plugin.
    
    `constructor(plugin: app.Plugin)`
    :   Initializes a new instance of this class
        
        - `plugin` - The plugin instance
        
    `readonly handle: app.Plugin`
    :   The plugin where this context belongs
        
        *This property is read-only*
        
    `cache: { [pathspec: string]: Exports }`
    :   Stores all exports of loaded modules
        
    `intent: any[]`
    :   Stores intents
        
    `reset(): void`
    :   Resets the context
        

#### Types

`type app.Require = (path: string) => app.Exports`
:   A require function
    
`type app.Exports = any`
:   Module.prototype.exports representation
    
`type app.LibObject = { [pathspec: string]: app.ModuleFunct | app.Module }`
:   An uncompiled lib object
    
`type app.CompiledLib = { [pathspec: string]: app.Module }`
:   A compiled lib object
    
`type ModuleFunct = (this: app.Module, api: app.Context, require: app.Require, module: app.Module, exports: app.Exports) => void`
:   A module action

## Writing a plugin

Now you are ready to write plugins! Here is the examples of basic usage of the Plugin API.

#### Creating a plugin

```typescript
import creator from "./framework/index.js";

const plugin = new creator.app.Plugin("myplugin", function(api, require, module, exports) {
    console.log("Hello world!")
  });
```

#### Plugin package

```typescript
import creator from "./framework/index.js";

const plugin = new creator.app.Plugin("myplugin", {
    "a/b/c": function(api, require, module, exports) {
      module.exports = "Hello world!";
    },
    "a/index": function(api, require, module, exports) {
      // export message from "a/b/c"
      exports.msg = require("./b/c");
      require("../normal/path"); // loads the last module below
    },
    "custom/entry/path": function(api, require, module, exports) {
      // destruction
      const { msg } = require("../../a"); // resolves "a" as a package: a/index
      console.log(msg);
    },
    // support module path normalization
    "/lazy/../not///../normalized/.///..//normal/./path/.///.": function(api, require, module, exports) {
      console.log(module.path); // "normal/path"
    }
  })
    // set entry point
    .entry("custom/entry/path");

plugin.start()
// This will be the result in logs
// "normal/path"
// "Hello world!"
```

#### Plugin package with custom loader

```typescript
import creator from "./framework/index.js";

const loader = new creator.app.Loader();

// create custom module(s)
loader.create("path/to/module", function(api, require, module, exports) {
  console.log("Module ran!")
  require("/index");
});

loader.create("index", new creator.app.Module(loader, "index", function(api, require, module, exports) {
    console.log("loaded!")
  })
)

loader.entry = "/path/to/module"; // set entry point

// create plugin
const plugin = new creator.app.Plugin("myplugin", loader);

plugin.start(); // logs "Module ran!" and "loaded!"
```

#### Registring a plugin

```typescript
import creator from "./framework/creator";

const plugin = new creator.app.Plugin("myplugin", function(api, require, module, exports) {
    exports.customExport = "Hi there";
  });

// This will work:
plugin.start(); // { customExport: "Hi there" }

// But not with "load" function:
creator.app.load("myplugin"); // throws an error: "Plugin 'myplugin' not exists or isn't registered!"

// We need to register it first to global registry:
plugin.register();

// This will now work:
creator.app.load("myplugin"); // { customExport: "Hi there" }

// Note:  Once your plugin was registered, it can be accessed by other plugins
```

#### Resetting app objects

```typescript
import creator from "./framework/index.js";

// a plugin instance
const plugin = creator.app.Plugin("myplugin", function(api, require, module, exports) {
  // indicates the plugin was re-runned when logged
  console.log("plugin ran!");
  /* the following will throw an error when called while the plugin are running
  module.reset();
  module.loader.reset();
  module.loader.plugin.reset();
  */
});

// run the plugin
plugin.start(); // logs "plugin ran!"

// running again
plugin.start();
// will not take effect because the plugin has already been cached, need to reset
// it first

// resets whole plugin
plugin.reset();

// resets only the plugin context
plugin.context.reset();

// reset all modules and `plugin.context.cache`
plugin.loader.reset();

// reset one module
plugin.loader.modules["index"].reset();

// after reseting, you can call the plugin again
plugin.start(); // logs "plugin ran!"
```
