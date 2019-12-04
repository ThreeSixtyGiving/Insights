import React from 'react';

export const DashboardFooter = function(props) {
    return <div>
        <footer className="light">
            <ul className="footer__social">
                <li><a href="https://github.com/ThreeSixtyGiving/"><img src="/images/icon-github.png"
                    title="Github" /></a></li>
                <li><a href="https://twitter.com/360giving"><img src="/images/icon-twitter.png"
                    title="Twitter" /></a></li>
            </ul>
            <div className="flex-wrapper">
                <section>
                    <div className="footer__navigation--title">
                        &nbsp;
                                    <ul className="footer__navigation">
                            <li><a href="https://www.threesixtygiving.org/contact/">Contact</a></li>
                        </ul>
                    </div>
                </section>
                <section>
                    <ul className="footer__navigation footer__navigation--headless">
                        <li><a href="/about">About</a></li>
                    </ul>
                </section>
                <section>
                    <p style={{ fontWeight: 300 }}>
                        <a href="https://www.threesixtygiving.org/">
                            <img src="/images/360giving-white@4x.png" style={{ opacity: 0.5 }} width="192" /><br />
                        </a>
                        Open data for more effective grantmaking
                                </p>
                </section>
            </div>
            <div className="footer__divider">
                <hr />
                <div className="footer__divider__columns">
                    <p>
                        <a href="/about#privacy">Privacy Notice</a> |
                                    <a href="/about#terms">Terms &amp; Conditions</a> |
                                    <a href="/about#cookies">Cookie Policy</a><br />
                        <a href="http://www.threesixtygiving.org/take-down-policy/">Take Down Policy</a> |
                                    <a href="https://creativecommons.org/licenses/by/4.0/">License</a>
                    </p>
                    <p className="footer__credits">
                        Created by <a href="https://dkane.net" rel="noopener" target="_blank">David Kane</a>.
                                    Design by <a href="https://www.ccmdesign.ca/" rel="noopener"
                            target="_blank">ccm.design</a><br />
                        360Giving: Company <a href="https://beta.companieshouse.gov.uk/company/09668396"
                            rel="noopener" target="_blank">09668396</a>
                        Charity <a
                            href="http://beta.charitycommission.gov.uk/charity-details/?regid=1164883&amp;subid=0"
                            rel="noopener" target="_blank">1164883</a>
                    </p>
                </div>
            </div>
        </footer>
    </div>
}
