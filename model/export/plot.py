
from model.export.utils import Plot


def full_plot(m, filename):

    plot = Plot(m, horizontal_spacing=0.02, vertical_spacing=0.05)
    
    plot.add(lambda t,r: m.baseline(t, r), row=1, is_fct=True, name='baseline_emissions')
    plot.add(m.regional_emissions, row=1)
    plot.add(m.carbonprice, row=1, secondary_y=True)
    plot.add(m.adapt_costs, row=2, stackgroup='costs')
    plot.add(m.resid_damages, row=2, stackgroup='costs')
    plot.add(m.rel_abatement_costs, row=2, stackgroup='costs')
    plot.add(m.gross_damages, row=2)
    plot.add(m.adapt_level, row=2, secondary_y=True, visible='legendonly')

    plot.add(m.capital_stock, row=3)
    plot.add(m.GDP_gross, row=3)
    plot.add(m.GDP_net, row=3)
    plot.add(m.abatement_costs, row=3)
    plot.add(m.global_emissions, is_regional=False, row=4)
    plot.add(m.temperature, is_regional=False, row=4, secondary_y=True)
    plot.add(m.cumulative_emissions, is_regional=False, row=4, visible='legendonly')
    plot.set_yaxes_titles(['GtCO<sub>2</sub>/yr','% GDP', 'trillion US$2005/yr', 'GtCO<sub>2</sub>/yr'])
    plot.set_layout()

    plot.fig.write_html('output/{}.html'.format(filename))