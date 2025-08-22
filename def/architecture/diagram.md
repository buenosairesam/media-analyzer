# Architecture Diagram Generation

## Files
- `system_architecture.dot` - Graphviz source file
- `architecture_diagram.svg` - Generated SVG diagram

## To Update Diagram

```bash
cd def/architecture
dot -Tsvg system_architecture.dot -o architecture_diagram.svg
```

## Design Patterns Shown

1. **Source Adapters** - Abstract different video input sources
2. **Execution Strategies** - Local vs distributed processing 
3. **Queue Segregation** - Separate workers for different analysis types
4. **Analysis Adapters** - Pluggable AI models

## Color Coding

- **Green (✓)** - Currently implemented
- **Yellow (○)** - Planned features
- **Dotted lines** - Inheritance/abstraction
- **Dashed lines** - Planned connections

## Update Process

When implementing new features:
1. Change color from `#fff3cd` (yellow/planned) to `#d4edda` (green/implemented)
2. Change edge style from `dashed` to `solid`
3. Regenerate SVG