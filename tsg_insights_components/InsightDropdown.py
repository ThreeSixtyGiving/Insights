# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class InsightDropdown(Component):
    """A InsightDropdown component.
Dropdown list of options

Keyword arguments:
- id (string; optional)
- options (list; optional): An array of options
- value (list; optional): The currently selected value
- className (string; optional): The class of the container (div)
- style (dict; optional): The style of the container (div)
- selectStyle (dict; optional): The style of the <select> element
- selectClassName (string; optional): The class of the <select> element
- multi (boolean; optional): Whether it's a multi select or not"""
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

    def __repr__(self):
        if(any(getattr(self, c, None) is not None
               for c in self._prop_names
               if c is not self._prop_names[0])
           or any(getattr(self, c, None) is not None
                  for c in self.__dict__.keys()
                  if any(c.startswith(wc_attr)
                  for wc_attr in self._valid_wildcard_attributes))):
            props_string = ', '.join([c+'='+repr(getattr(self, c, None))
                                      for c in self._prop_names
                                      if getattr(self, c, None) is not None])
            wilds_string = ', '.join([c+'='+repr(getattr(self, c, None))
                                      for c in self.__dict__.keys()
                                      if any([c.startswith(wc_attr)
                                      for wc_attr in
                                      self._valid_wildcard_attributes])])
            return ('InsightDropdown(' + props_string +
                   (', ' + wilds_string if wilds_string != '' else '') + ')')
        else:
            return (
                'InsightDropdown(' +
                repr(getattr(self, self._prop_names[0], None)) + ')')
