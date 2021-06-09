import { formatCurrency } from './filters.js';

export const mapboxMap = {
    props: ['container', 'markers', 'height'],
    data: function () {
        return {
            map: null,
            marker_layer: null,
            mapbox_access_token: MAPBOX_ACCESS_TOKEN,
        };
    },
    methods: {
        updateMarkers() {
            var component = this;

            this.marker_layer.clearLayers();

            if (!this.markers) {
                return;
            }

            // add each of the markers
            this.markers.forEach(function (g, index) {
                if (g.insightsGeoLat && g.insightsGeoLong) {
                    component.marker_layer.addLayer(
                        L.marker([g.insightsGeoLat, g.insightsGeoLong])
                            .bindPopup(`
                                <table style="margin-bottom: 0px;" class="table">
                                    <tr><th style="">From</th><td>${L.mapbox.sanitize(g["fundingOrganizationName"])}</td></tr>
                                    <tr><th style="">To</th><td>${L.mapbox.sanitize(g["recipientOrganizationName"])}</td></tr>
                                    <tr><th style="">Amount</th><td>${L.mapbox.sanitize(formatCurrency(g["amountAwarded"], g["currency"], false))}</td></tr>
                                    <tr><th style="">Awarded</th><td>${L.mapbox.sanitize(g["awardDate"])}</td></tr>
                                </table>
                            `)
                    );
                }
            });

            // fit the map to the bounds of the marker
            this.map.fitBounds(this.marker_layer.getBounds(), { maxZoom: 9 });
        }
    },
    watch: {
        markers: {
            handler: function () {
                this.updateMarkers();
            },
            deep: true,
        },
    },
    mounted() {
        L.mapbox.accessToken = this.mapbox_access_token;
        var map = L.mapbox.map(this.container, null, {
            attributionControl: { compact: true },
            zoomControl: true,
        }).setView([52.9225, 1.4746], 6);
        L.mapbox.styleLayer('mapbox://styles/davidkane/cjvnt2h0007hm1clrbd20bbug').addTo(map)

        // disable scroll when map isn't focused
        map.scrollWheelZoom.disable();
        map.on('focus', function () { map.scrollWheelZoom.enable(); });
        map.on('blur', function () { map.scrollWheelZoom.disable(); });

        // ensure mapbox logo is shown (for attribution)
        document.querySelector('.mapbox-logo').classList.add('mapbox-logo-true');

        // create the marker cluster object that will hold the markers
        this.marker_layer = L.markerClusterGroup({
            singleMarkerMode: true,
            polygonOptions: {
                color: '#4DACB6'
            }
        }).addTo(map);

        // add the layer controls
        L.control.groupedLayers({}, getOverlays(this.marker_layer, map), {
            exclusiveGroups: ["Overlay data", "Boundaries"],
            collapsed: true,
            hideSingleBase: true,
        }).addTo(map);

        this.map = map;
        this.updateMarkers();
    },
    template: '<div v-bind:id="container" v-bind:style="{ height: height }"></div>'
}

// layers that will be displayed in the data
function getOverlays(markers, map) {

    // set up attribution for deprivation layer
    var deprivation_options = {
        opacity: 0.8,
        attribution: '<strong>Deprivation</strong>: <a href="https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019" target="_blank">English Indices of Deprivation</a> (<a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">OGL</a>)<br>'
    }
    map.attributionControl.addAttribution(deprivation_options['attribution']);

    // set up attribution for boundary layer
    var boundary_attribution = `<br><strong>Boundaries</strong>: <a href="http://geoportal.statistics.gov.uk/" target="_blank">Office for National Statistics</a>  (<a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">OGL</a>)<br>' +
        'Contains OS data © Crown copyright and database right ${new Date().getFullYear()}`;

    // function for determining style of boundaries
    var boundary_options = function (style) {
        var defaultStyle = { fillOpacity: 0.05, color: '#4DACB6', opacity: 0.6, weight: 1 };
        return {
            style: Object.assign({}, defaultStyle, style),
            attribution: boundary_attribution,
        }
    }

    // function for showing the name of an area
    var boundary_name_field = function (layer) {
        var name_field = Object.keys(layer.feature.properties).find(el => el.endsWith("nm"));
        return layer.feature.properties[name_field];
    }

    return {
        "Grants data": {
            "Grants": markers,
            'All charities': L.mapbox.styleLayer('mapbox://styles/davidkane/ck36gljmp1tj11cmujpokrea1'),
        },
        "Overlay data": {
            "No overlay": L.mapbox.featureLayer(null).addTo(map),
            'Deprivation (England - IMD2019 ranks)': L.mapbox.styleLayer('mapbox://styles/davidkane/ck309ufnq0rrx1csftj9515ze', deprivation_options),
            '- Income': L.mapbox.styleLayer('mapbox://styles/davidkane/ck35t6us210271cmlswr7ic2m', deprivation_options),
            '- Employment': L.mapbox.styleLayer('mapbox://styles/davidkane/ck30abu8r0b511cqjl7gnb835', deprivation_options),
            '- Education': L.mapbox.styleLayer('mapbox://styles/davidkane/ck30acrnp0s621coaemmp19rm', deprivation_options),
            '- Health': L.mapbox.styleLayer('mapbox://styles/davidkane/ck30afwq40s4p1claktbbm3gk', deprivation_options),
            '- Crime': L.mapbox.styleLayer('mapbox://styles/davidkane/ck35t8f1z03zg1cpiltsec9ep', deprivation_options),
            '- Barriers to Housing & Services': L.mapbox.styleLayer('mapbox://styles/davidkane/ck30agq740bah1co9csdf1yu5', deprivation_options),
            '- Living Environment': L.mapbox.styleLayer('mapbox://styles/davidkane/ck30ahvkn0be01dmu0r75ryvj', deprivation_options),
            '- Most deprived 20%': L.mapbox.styleLayer('mapbox://styles/davidkane/ck30nnfoj0mj61cpnxh7ijw06', deprivation_options),
            'Deprivation (Wales - WIMD2019 deciles)': L.mapbox.styleLayer('mapbox://styles/davidkane/ck3ymy7fu0de91cp8grzu8ft7', {
                opacity: 0.8,
                attribution: '<strong>Deprivation Wales</strong>: <a href="https://statswales.gov.wales/Catalogue/Community-Safety-and-Social-Inclusion/Welsh-Index-of-Multiple-Deprivation/WIMD-2019" target="_blank">WIMD 2019</a> (<a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">OGL</a>)<br>'
            }),
            'Deprivation (Scotland - SIMD16 deciles)': L.mapbox.styleLayer('mapbox://styles/davidkane/ck3z2ozhn2ir71cmqdnnpc6ty', {
                opacity: 0.8,
                attribution: '<strong>Deprivation Scotland</strong>: <a href="https://www2.gov.scot/Topics/Statistics/SIMD" target="_blank">SIMD16</a> (<a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">OGL</a>)<br>'
            }),
            'Deprivation (Northern Ireland - NIMDM17 deciles)': L.mapbox.styleLayer('mapbox://styles/davidkane/ck3z3hapk56l11cmwuwswq766', {
                opacity: 0.8,
                attribution: '<strong>Deprivation NI</strong>: <a href="https://www.nisra.gov.uk/publications/nimdm17-soa-level-results" target="_blank">NIMDM17</a> (<a href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/">OGL</a>)<br>'
            }),
        },
        "Boundaries": {
            "No boundaries": L.mapbox.featureLayer(null).addTo(map),
            'Country and Region': L.mapbox.featureLayer(null, boundary_options({ weight: 2 }))
                .loadURL('/static/geo/country_region.geojson')
                .bindPopup(boundary_name_field),
            'Local Authorities': L.layerGroup([
                // Local Authority (lower tier)
                L.mapbox.featureLayer(null, boundary_options({
                    fillOpacity: 0.05,
                    opacity: 0.3,
                    weight: 1
                }))
                    .loadURL('/static/geo/lalt.geojson')
                    .bindPopup(boundary_name_field),
                // Local Authority (upper tier)
                L.mapbox.featureLayer(null, boundary_options({
                    fill: false,
                    clickable: false,
                    opacity: 1,
                    weight: 1.5
                }))
                    .loadURL('/static/geo/laut.geojson'),
            ]).bindPopup(boundary_name_field),
            'Parliamentary Constituencies': L.mapbox.featureLayer(null, boundary_options())
                .loadURL('/static/geo/pcon.geojson')
                .bindPopup(boundary_name_field),
            'Clinical Commissioning Groups (England)': L.mapbox.featureLayer(null, boundary_options())
                .loadURL('/static/geo/ccg.geojson')
                .bindPopup(boundary_name_field),
            'Local Enterprise Partnerships (England)': L.mapbox.featureLayer(null, boundary_options({
                fillOpacity: 0.3
            }))
                .loadURL('/static/geo/lep.geojson')
                .bindPopup(boundary_name_field),
        }
    }
};