# SEG-12 Reconciled Analysis
**Lines**: L2047-2210
**Description**: Option widget class (bool/int/list option display and navigation)

## Purpose
Option is a UI widget representing a single configurable option. It supports three types: bool (true/false), int (bounded or unbounded integer), and list (enumeration of string values). The widget handles left/right key navigation to change the value and renders itself as `◀ value ▶` with arrow indicators.

## Line Walkthrough
- **L2051-2064**: `hasPrevious(self)` — bool: always true; int: `value > min` (if min set); list: `value > 1`.
- **L2065-2078**: `hasNext(self)` — bool: always true; int: `value < max` (if max set); list: `value < #possibleValues`.
- **L2079-2093**: `leftKey(self)` — bool: toggles; int: decrements (by step or 1); list: decrements index.
- **L2094-2108**: `rightKey(self)` — bool: toggles; int: increments; list: increments index.
- **L2109-2123**: `getValue(self)` — bool/int: returns `self.value`; list: returns `possibleValues[i][1]` (the key).
- **L2124-2144**: `setValue(self, value)` — bool/int: direct assign; list: searches possibleValues for matching [1] element, sets index; logs warning if not found.
- **L2146-2163**: `getDisplayValue(self)` — bool: "yes"/"no"; int: `altDisplayNames[v]` or `tostring(v)`; list: `possibleValues[i][2]` (display name) or key.
- **L2165-2178**: `draw(self, ass, selected)` — renders with bold if selected; shows ◀ and ▶ arrows if has prev/next.
- **L2180-2186**: `optVisible(self)` — returns `visibleCheckFn()` if set, else true.
- **L2190-2196**: `__init(self, optType, displayText, value, opts, visibleCheckFn)` — sets type, display, calls setValue.

## Data Structures
- `opts` for int: `{min=N, max=N, step=N, altDisplayNames={[v]="name"}}` (all optional).
- `opts` for list: `{possibleValues={{key, displayName}, ...}}`.
- `opts` for bool: unused.

## Edge Cases
- Bool `leftKey`/`rightKey` both toggle the value — they are equivalent (not directional).
- Int with no min/max: hasPrevious/hasNext always true — infinite range.
- List getValue crashes if `possibleValues` is nil or empty.
- setValue for list: warning only on invalid value; `self.value` remains 1 (initial).
- `visibleCheckFn` can hide options conditionally (e.g., hide twopass for formats that don't support it).

## mpv Interactions
None in this segment.
