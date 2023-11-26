# Tell Me Why

https://github.com/SuperFLEB/blender_tell_me_why

A Blender addon that lets you show the math and take notes on your nodes, so you're never left wondering _exactly why_
you set the scale on that input to 21.887.

## Features

* Add descriptive annotations to node socket values
* Use formulas that calculate socket default values
* Formulas and annotations are saved with the Blender file
* Scene-wide variables for use in formulas and values

### Future Features, Coming Soon

* Import/export formulas and values to files or to a personal library

## To install

Either install the ZIP file from a release or clone this repository and use the build_release.py script to build a ZIP
that you can install into Blender.

## To use

Whenever you select a node in a node editor, you'll find a new Tell Me Why tab in the N-panel. Click the "+" to add
annotations, then the pencil icon to edit the annotation. You can add notes (text fields marked with the "i" icon) or
toggle the "f(x)" icon to add a formula or value. Formulas can use mathematical operators, functions and constants. If
the value of the node socket changes from the formula, click the "Apply" button to re-run the formula and set the value,
or use "File > Apply All Formulas" to apply formulas everywhere in the file. 
