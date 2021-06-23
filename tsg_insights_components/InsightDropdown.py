# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class InsightDropdown(Component):
    """An InsightDropdown component.
Dropdown list of options

Keyword arguments:
- id (string; optional)
- options (dict; optional): An array of options. options has the following type: list of dicts containing keys 'label', 'value', 'disabled'.
Those keys have the following types:
  - label (string; optional): The checkbox's label
  - value (string; optional): The value of the checkbox. This value
corresponds to the items specified in the
`value` property.
  - disabled (boolean; optional): If true, this checkbox is disabled and can't be clicked on.
- value (list of strings; optional): The currently selected value
- className (string; optional): The class of the container (div)
- style (dict; optional): The style of the container (div)
- selectStyle (dict; optional): The style of the <select> element
- selectClassName (string; default ''): The class of the <select> element
- multi (boolean; default False): Whether it's a multi select or not"""
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, options=Component.UNDEFINED, value=Component.UNDEFINED, className=Component.UNDEFINED, style=Component.UNDEFINED, selectStyle=Component.UNDEFINED, selectClassName=Component.UNDEFINED, multi=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'options', 'value', 'className', 'style', 'selectStyle', 'selectClassName', 'multi']
        self._type = 'InsightDropdown'
        self._namespace = 'tsg_insights_components'
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'options', 'value', 'className', 'style', 'selectStyle', 'selectClassName', 'multi']
        self.available_wildcard_properties =            []

        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in []:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')
        super(InsightDropdown, self).__init__(**args)
