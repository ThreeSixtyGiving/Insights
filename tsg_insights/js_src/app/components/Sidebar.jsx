import React from 'react';

import { FilterForm } from './FilterForm.jsx';

export const Sidebar = function(props) {
    return <aside className="results-page__menu">
        <a href="/?file-selection-modal" className="results-page__menu__back"><i className="material-icons">arrow_back</i>
            Select another dataset</a>
        <h3 className="results-page__menu__section-title">Filters</h3>
        <FilterForm />
    </aside>
}
