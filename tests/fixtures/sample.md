# Test Document with Mermaid Diagrams

This is a test document containing multiple Mermaid diagrams.

## Basic Flowchart

```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[Decision]
    C -->|Yes| D[Action 1]
    C -->|No| E[Action 2]
    D --> F[End]
    E --> F
```

## Sequence Diagram with Theme

```mermaid {theme: dark}
sequenceDiagram
    participant Alice
    participant Bob
    participant Charlie

    Alice->>Bob: Hello Bob, how are you?
    Bob-->>Alice: Great thanks!
    Bob->>Charlie: How about you Charlie?
    Charlie-->>Bob: Awesome!
```

## Class Diagram

```mermaid
classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
    class Dog {
        +String breed
        +bark()
    }
    class Cat {
        +String color
        +meow()
    }

    Animal <|-- Dog
    Animal <|-- Cat
```

## Some Regular Content

This is just regular markdown content that should not be affected by the plugin.

### Code Block (Not Mermaid)

```python
def hello_world():
    print("Hello, World!")
```

## Another Mermaid Diagram

```mermaid
pie title Pet Distribution
    "Dogs" : 386
    "Cats" : 85
    "Birds" : 15
    "Fish" : 14
```
