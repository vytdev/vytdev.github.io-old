---
title: threading - API Reference
about: Module for making threads
contributors: VYT <https://github.com/vytdev>
---

This module implements a thread-based parallelism or multi-threading, based on the
python module `threading`. What is multi-threading? Multi-threading is a strategy
to run multiple tasks on the CPU cores to fasten its work. However, JavaScript doesn't
support it as its only single-threaded, means it runs code only on the main thread.
And thats why this module was created for! This simulates multi-threading based on
Minecraft ticks or the in-game loops.

#### Functions

`function threading.getThread(key: number | string): threading.Thread | null`
:   Returns a thread by ID or custom name
    
    - `key` - The thread ID or name to retrieve
    
    Returns a thread object, or `null` if not found

#### Classes

`class threading.Thread`
:   The main thread class
    
    `constructor(name?: string)`
    :   Initializes a new instance of this class
        
        - `name` - Optional name to assign to the thread
        
    `readonly name?: string`
    :   The name of the thread, maybe `undefined`
        
    `readonly id: number`
    :   Unique identifier for the thread
        
    `get task: Generator | null`
    `set task(val: Generator | null)`
    :   The task running on the thread, can be `null` when thread is not alive
        
    `get alive(): boolean`
    :   Returns whether the thread is alive
        
    `get active(): boolean`
    :   Returns whether the thread is active
        
    `funct(fn: threading.ThreadGenerator): this`
    :   Sets a new thread function
        
        - `fn` - The generator function to set in
        
        Returns the thread itself.
        
    `start(...args: any): this`
    :   Starts the thread task, with optional arguments.
        
        - `args` - Optional arguments to pass on the thread task
        
        Returns the thread itself.
        
    `stop(): this`
    :   Stops the thread
        
        Returns the thread itself.
        
    `join(): this`
    :   Wait the thread execution until terminates, ignoring if the thread aquired
        a lock. This will block the main thread.
        
        Returns the thread itself.
        
    `lock(val?: boolean): boolean`
    :   Locks or unlocks the thread. Or simply pause and continue the thread execution.
        
        - `val` - Set the current lock state of the thread
        
        Returns the current lock state.
        
    `delay(count?: number): this | number`
    :   Delays the interval execution of thread
        
        - `count` - The delay in ticks, don't specify to return the current delay
        
        Returns the thread itself when count parameter is specified.
        
    `wait(condition: threading.Condition): this`
    :   Wait for a timeout or condition to finish. Aquires a lock, wait for the condition
        and release after.
        
        - `condition` - The condition to wait for
        
        If the `condition` is a function, it will be called everytime until returned
        `true`. But if the condition is a number, wait a timeout in ticks.
        
        Returns the thread itself.
        
    `run(val?: any): IteratorResult<any>`
    :   Run thread until next `yield` keyword
        
        - `val` - Optional value to pass to the generator
        
        Returns iterator result object.
        
    `except(err: any): IteratorResult<any>`
    :   Throws an error from the body of the Generator task
        
        - `err` - The error to pass
        
        Returns iterator result object.
        

#### Types

`type threading.ThreadGenerator = (...args: any) => Generator<unknown>`
:   Thread generator type

`type threading.Condition = (() => boolean) | number | null`
:   Condition type

## Configurations

- `threadBuffer` - How many threads to execute at a time. `512` by default.
    
    !!! warning
        
        Setting to a higher value may cause the game to lag!

## As plugin

This module is also available as a [plugin](./app.html). It is defined as the `threading`
library:

```typescript
// requiring the threading library
const events = require("threading");
```

Remember that the types aren't available from a require.
