openerp.account.graph_kanban = function (instance)
{   
    var _t = instance.web._t,
   _lt = instance.web._lt;
    instance.web_kanban.JournalDashboardGraph = instance.web_kanban.AbstractField.extend({
        start: function() {
            var self = this;
            self.journal_type = self.$node.attr('journal_type')
            self.display_graph(self.field.raw_value);
        },
        display_graph : function(data) {
            var self = this;
            nv.addGraph(function () {
                self.$el.append('<svg>');
                if (self.journal_type === 'cash' || self.journal_type === 'bank') {
                    var chart = nv.models.lineChart()
                        .x(function (d,u) { return u })
                        .forceY([0, 100])
                        .width(300)
                        .height(225);
                    chart.xAxis
                        .tickFormat(function(d) {
                            return data.values[d] && data.values[d].x || '';
                        })
                        .rotateLabels(35)
                        .showMaxMin(false);

                } else {
                    var chart = nv.models.multiBarChart()
                        .width(335)
                        .height(240)
                        .showControls(false)
                        .rotateLabels(35)
                        .forceY([0, 100])
                        .reduceXTicks(false);
                }
                self.svg = self.$el.find('svg')[0];
                d3.select(self.svg)
                    .datum([data])
                    .transition().duration(1200)
                    .call(chart);
                nv.utils.windowResize(function() { d3.select(self.svg).call(chart) });
            });
        },
    });
    instance.web_kanban.fields_registry.add("journal_dashboard_graph", "instance.web_kanban.JournalDashboardGraph");
};
