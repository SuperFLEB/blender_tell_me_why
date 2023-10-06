# Tell Me Why

https://github.com/SuperFLEB/blender_tell_me_why

A Blender addon that lets you show the math and take notes on your nodes, so you're never left wondering _exactly why_
you set the scale on that input to 21.887.

_This addon is in early stages and active development. Feedback is welcome._

## Features

* Add descriptive reminders to nodes and inputs
* Use formulas to calculate values
* Save information with the Blender file

### Future Features, Coming Soon

* Reusable formulas and values


## To install

Either install the ZIP file from a release or clone this repository and use the build_release.py script to build a ZIP
that you can install into Blender.

## To use

Whenever you select a node in a node editor, you'll find a new Tell Me Why tab in the N-panel. Click the "+" to add
annotations, then the pencil icon to edit the annotation. You can add notes (text fields marked with the "i" icon) or
toggle the "f(x)" icon to add a formula or value. Formulas can use mathematical operators, functions and constants. If
the value of the node socket changes from the formula, click the "Apply" button to re-run the formula and set the value,
or use "File > Apply All Formulas" to apply formulas everywhere in the file. 

## Testing

_Tests are currently not implemented._

To run unit tests, run (from the Blender install directory):

```shell
blender --factory-startup --background --python path/to/module/run_tests.py
```
