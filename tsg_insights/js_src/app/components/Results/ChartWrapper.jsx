import React from 'react';

export const ChartTitle = function (props) {

    return <figcaption className={props.className}>
        <h2 className='results-page__body__section-title'>{props.title}</h2>
        <p className='results-page__body__section-subtitle'>{props.subtitle}</p>
        <div className='results-page__body__section-description'>{props.children}</div>
    </figcaption>
}

export const ChartWrapper = function (props) {

    return <figure className={props.className}>
        <ChartTitle title={props.title} subtitle={props.subtitle} />
        {props.children}
    </figure>
}