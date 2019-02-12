# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class InsightFoldable(Component):
    """A InsightFoldable component.
An element that can be hidden by clicking on the `title`
element. The `value` text is shown when hidden, otherwise
`children` are displayed.

Keyword arguments:
- children (a list of or a singular dash component, string or number; optional): The children of this component
- id (string; optional)
- container (optional): The container for the item. container has the following type: dict containing keys 'value', 'className', 'foldedClassName', 'unfoldedClassName', 'style'.
Those keys have the following types: 
  - value (string; optional): string shown in the title (h4)
  - className (string; optional): name of the class
  - foldedClassName (string; optional): class applied when folded
  - unfoldedClassName (string; optional): class applied when unfolded
  - style (dict; optional): The style applied
- title (optional): The title of the item (click this to toggle). title has the following type: dict containing keys 'value', 'className', 'foldedClassName', 'unfoldedClassName', 'style'.
Those keys have the following types: 
  - value (string; optional): string shown in the title (h4)
  - className (string; optional): name of the class
  - foldedClassName (string; optional): class applied when folded
  - unfoldedClassName (string; optional): class applied when unfolded
  - style (dict; optional): The style applied
- value (optional): The value (shown when the children are hidden). value has the following type: dict containing keys 'value', 'className', 'foldedClassName', 'unfoldedClassName', 'style'.
Those keys have the following types: 
  - value (string; optional): string shown in the title (h4)
  - className (string; optional): name of the class
  - foldedClassName (string; optional): class applied when folded
  - unfoldedClassName (string; optional): class applied when unfolded
  - style (dict; optional): The style applied
- child (optional): The child (shown when the item is toggled). child has the following type: dict containing keys 'value', 'className', 'foldedClassName', 'unfoldedClassName', 'style'.
Those keys have the following types: 
  - value (string; optional): string shown in the title (h4)
  - className (string; optional): name of the class
  - foldedClassName (string; optional): class applied when folded
  - unfoldedClassName (string; optional): class applied when unfolded
  - style (dict; optional): The style applied

Available events: """
    @_explicitize_args
    def __init__(self, children=None, id=Component.UNDEFINED, container=Component.UNDEFINED, title=Component.UNDEFINED, value=Component.UNDEFINED, child=Component.UNDEFINED, **kwargs):
        self._prop_names = ['children', 'id', 'container', 'title', 'value', 'child']
        self._type = 'InsightFoldable'
        self._namespace = 'tsg_insights_components'
        self._valid_wildcard_attributes =            []
        self.available_events = []
        self.available_properties = ['children', 'id', 'container', 'title', 'value', 'child']
        self.available_wildcard_properties =            []

        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs
        args = {k: _locals[k] for k in _explicit_args if k != 'children'}

        for k in []:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')
        super(InsightFoldable, self).__init__(children=children, **args)

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
            return ('InsightFoldable(' + props_string +
                   (', ' + wilds_string if wilds_string != '' else '') + ')')
        else:
            return (
                'InsightFoldable(' +
                repr(getattr(self, self._prop_names[0], None)) + ')')
