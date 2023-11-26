# Tell Me Why

![Tell Me Why: Node Annotations for Blender](doc_support/tmy_banner.png)

https://github.com/SuperFLEB/blender_tell_me_why

A Blender addon that lets you show the math and take notes on your nodes, so you're never left wondering _exactly why_
you set the scale on that input to 21.887.

## Features

* Add descriptive annotations to node socket values
* Use formulas that calculate socket default values
* Formulas and annotations are saved with the Blender file
* Scene-wide variables for use in formulas and values

### Future Features, Coming Soon

* Add a way to see annotations from the Node Editor top bar. 

## To install

Either install the ZIP file from a release or clone this repository and use the build_release.py script to build a ZIP
that you can install into Blender.

## To use

### Annotations and Formulas

Whenever you select a node in a node editor, you'll find a new Tell Me Why tab in the N-panel. Click the "+" to add
annotations, then the pencil icon to edit the annotation. You can add notes (text fields marked with the "i" icon) or
toggle the "f(x)" icon to switch between using the value from the node, or setting a formula or value.
Formulas can include mathematical operators, functions, and constants. If the value of the node socket changes from
the formula, click the "Apply" button to re-run the formula and set the value, or use "File > Apply All Formulas" to
apply formulas everywhere in the file. 

You can also set the Tell Me Why panel to appear in the Node tab. Just look in the addon's Preferences panel. 

### Variables

Variables allow you to use the same named value in formulas throughout your Scene, without needing to remember exact
values each time or update multiple places if a common value changes. Variables can be found in the Tell Me Why panel,
and can be set to a number or a list (e.g., `(1, 2, 3)`). Their formulas can use built-in names and functions, but
cannot reference other variables.

*Please note: Variables exist on the Scene level, not the .blend-file level. (This is due to a limitation
in Blender that you can't attach data to the document as a whole, only a Scene.) You can easily copy all variables from
another Scene using the "Import Variables From..." feature, but it does need to be done manually.*

#### The Variable Library

If you've got variables you use often, you can put them in the Variable Library, in the addon's Preferences panel. These
are stored with your Blender preferences, and can be imported into any Scene. *Note that the Library is only for import,
and Library values must be imported to be used. Updates to the Library variables must be re-imported to be reflected in
files and scenes.*