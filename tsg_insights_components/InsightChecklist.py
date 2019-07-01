# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class InsightChecklist(Component):
    """A InsightChecklist component.
Checklist is a component that encapsulates several checkboxes.
The values and labels of the checklist is specified in the `options`
property and the checked items are specified with the `value` property.
Each checkbox is rendered as an input with a surrounding label.

Keyword arguments:
- id (string; optional)
- options (optional): An array of options. options has the following type: list of dict containing keys 'label', 'value', 'disabled'.
Those keys have the following types:
  - label (string; optional): The checkbox's label
  - value (string; optional): The value of the checkbox. This value
corresponds to the items specified in the
`value` property.
  - disabled (boolean; optional): If true, this checkbox is disabled and can't be clicked on.s
- value (list of strings; optional): The currently selected value
- className (string; optional): The class of the container (fieldset)
- style (dict; optional): The style of the container (fieldset)
- ulStyle (dict; optional): The style of the <ul> container element
- ulClassName (string; optional): The class of the <ul> container element
- liStyle (dict; optional): The style of the <li> element
- liClassName (string; optional): The class of the <li> element
- inputStyle (dict; optional): The style of the <input> checkbox element
- inputClassName (string; optional): The class of the <input> checkbox element
- labelStyle (dict; optional): The style of the <label> that wraps the checkbox input
 and the option's label
- labelClassName (string; optional): The class of the <label> that wraps the checkbox input
 and the option's label"""
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, options=Component.UNDEFINED, value=Component.UNDEFINED, className=Component.UNDEFINED, style=Component.UNDEFINED, ulStyle=Component.UNDEFINED, ulClassName=Component.UNDEFINED, liStyle=Component.UNDEFINED, liClassName=Component.UNDEFINED, inputStyle=Component.UNDEFINED, inputClassName=Component.UNDEFINED, labelStyle=Component.UNDEFINED, labelClassName=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'options', 'value', 'className', 'style', 'ulStyle', 'ulClassName', 'liStyle', 'liClassName', 'inputStyle', 'inputClassName', 'labelStyle', 'labelClassName']
        self._type = 'InsightChecklist'
        self._namespace = 'tsg_insights_components'
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'options', 'value', 'className', 'style', 'ulStyle', 'ulClassName', 'liStyle', 'liClassName', 'inputStyle', 'inputClassName', 'labelStyle', 'labelClassName']
        self.available_wildcard_properties =            []

        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in []:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')
        super(InsightChecklist, self).__init__(**args)
