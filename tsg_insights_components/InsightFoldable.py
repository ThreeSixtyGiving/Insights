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
- title (string; optional): The title of the item (click this to toggle)
- value (string; optional): The item shown if hidden
- className (string; optional): The class of the container (div)
- style (dict; optional): The style of the container (div)
- titleStyle (dict; optional): The style of the <h4> title element
- titleClassName (string; optional): The class of the <h4> title element
- titleFoldedClassName (string; optional): The class of the <h4> title element when folded
- titleUnfoldedClassName (string; optional): The class of the <h4> title element when unfolded
- valueStyle (dict; optional): The style of the <h5> value element - shown if main element is hidden
- valueClassName (string; optional): The class of the <h5> value element - shown if main element is hidden"""
    @_explicitize_args
    def __init__(self, children=None, id=Component.UNDEFINED, title=Component.UNDEFINED, value=Component.UNDEFINED, className=Component.UNDEFINED, style=Component.UNDEFINED, titleStyle=Component.UNDEFINED, titleClassName=Component.UNDEFINED, titleFoldedClassName=Component.UNDEFINED, titleUnfoldedClassName=Component.UNDEFINED, valueStyle=Component.UNDEFINED, valueClassName=Component.UNDEFINED, **kwargs):
        self._prop_names = ['children', 'id', 'title', 'value', 'className', 'style', 'titleStyle', 'titleClassName', 'titleFoldedClassName', 'titleUnfoldedClassName', 'valueStyle', 'valueClassName']
        self._type = 'InsightFoldable'
        self._namespace = 'tsg_insights_components'
        self._valid_wildcard_attributes =            []
        self.available_properties = ['children', 'id', 'title', 'value', 'className', 'style', 'titleStyle', 'titleClassName', 'titleFoldedClassName', 'titleUnfoldedClassName', 'valueStyle', 'valueClassName']
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
