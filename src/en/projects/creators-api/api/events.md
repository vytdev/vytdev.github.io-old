---
title: events - API Reference
about: A simple module for creating and handling events
contributors: VYT <https://github.com/vytdev>
---

Events are very useful for communicating with every part of the add-on scripts.
This article shows the reference for the `events` module in the Creators’ API
framework. This module is based on the DOM Events implementation and the `EventEmitter`
class from [notbeer's](https://github.com/notbeer) Minecraft script library
[Gametest API Wrapper](https://github.com/notbeer/Gametest-API-Wrapper). Here's
how to use it.

#### Classes

`class events.EventsHandler`
:   The main event emitter class
    
    `[staticListener: events.StaticListenerKey]: events.EventListener`
    :   Allows you to set listeners in the class like `handler.onevent`. All letters
        after the word `on` must be lower-cased.
    
    `listen(ev: string, action: events.EventListener, options?: events.EventOptions): number`
    :   Listen for an event
        
        - `ev` - The event name to listen for
        - `action` - The listener callable that is executed once the event was fired
        - `options` - Additional options for the listener
        
        Returns the listener ID, you **must not** use it with other handlers
        
    `dispatch(ev: string, ...args: any): events.EventContext`
    :   Triggers an event
        
        - `ev` - The event to fire
        - `args` - Objects to emit in all listeners
        
        Returns the context of the target event.
        
    `emit(...args: any): EventContext`
    :   Same as the `dispatch` method, but fires all listeners. Also ignores
        `once` listener option and cancelation of event propagation.
        
    `remove(id: number): boolean`
    :   Removes a listener
        
        - `id` - The listener ID to remove
        
        Returns `true` if succed
        
    `events(): string[]`
    :   Get all event names for all listeners
        
        Returns an array of event names
        

`class events.EventContext`
:   Event target class
    
    `constructor(ev: string)`
    :   Initialize a new instance of this class
        
        - `ev` - The event name this was for
        
    `readonly event: string`
    :   Name of the event passed to the constructor
        
    `propagate: boolean`
    :   Do event propagation. Runs next pending listeners. Default to `true`
        

#### Interfaces

`interface events.EventOptions`
:   An interface representing listener options
    
    `once: boolean`
    :   Whether only execute the listener once

#### Types

`` type events.StaticListenerKey = `on${string}` ``
:   Static event listener key names

`type events.EventListener = (this: events.EventContext, ...args: any) => unknown`
:   Representation of an event listener

#### Constants

`const events.MAIN: events.EventsHandler`
:   The main event handler

## As plugin

This module is also available as a [plugin](./app.html). It is defined as the `events`
library:

```typescript
// requiring the events library
const events = require("events");
```

Remember that the types aren't available from a require.
