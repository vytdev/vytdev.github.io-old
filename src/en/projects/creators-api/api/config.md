---
title: config - API Reference
about: Configuration options of the framework
contributors: VYT <https://github.com/vytdev>
---

#### Config class

`class config.Config<T extends object>`
:   A class for handling configs
    
    `constructor(data?: T)`
    :   Initialize a new instance of this class
        
    `get<K extends keyof T>(key: K): T[K]`
    :   Returns a config by key
        
        - `key` - The key to retrieve
        
        Returns the value of key
        
    `set<K extends keyof T>(key: K, val: T[K]): T[K]`
    :   Sets a config key
        
        - `key` - The config key to replace
        - `val` - New value to assign for the key
        
        Returns the parameter `val`
        
    `has(key: keyof T): boolean`
    :   Check if a config key exists
        
        - `key` - The key to Check
        
        Returns boolean, true if found
        
    `delete(key: keyof T): boolean`
    :   Unsets a stored config key
        
        - `key` - The key to delete
        
        Returns boolean, true if succed
        
    

#### Framework config

`default new Config()`
:   The default export containing the framework config. If you want to change the config,
    you should import it in a separate script and change it there instead of editing the
    file directly, like as shown below. This is because the config file may change at every
    release of an update of the framework. Editing the config file directly is not recomended
    when you're migrating with other versions of the add-on.
    
        :::typescript
        import config from "./framework/config.js";
        
        // update a config, without touching directly the config file
        config.set("exmapleConfig", true);
        
        // load the framework after modding config
        import("./framework/index.js");
        
        // Note:  Don't use the import literal because in ECMAScript spec, all imports, even it's in the
        // bottom of a script are executed before the content of that script.
    
    In the example above, we delayed the framework to update the config. But why?
    Because some config will not take effect once the framework was fully-loaded.
    
    `threadBuffer: number`
    :   Number of calls to do in every re-execution of threads. Default: `512`
    
