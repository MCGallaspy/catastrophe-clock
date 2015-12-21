var ClockView = Backbone.View.extend({
    render: function() {
        var pad = function(val, pad) {
                var len = val.toString().length;
                if (len < pad) {
                    return "0".repeat(pad - len) + val.toString();
                } else {
                    return val.toString();
                }
        };
        this.$el.html(this.template({
            days: pad(this.model.get("days"), 4),
            hours: pad(this.model.get("hours"), 2),
            minutes: pad(this.model.get("minutes"), 2),
            seconds: pad(this.model.get("seconds"), 2)
        }));
    },

    template: _.template("<%= days %>:<%= hours %>:<%= minutes %>:<%= seconds %>"),

    initialize: function(options) {
        _.bindAll(this, "render", "template", "update");
        this.model = options.model || new Backbone.Model();
        this.model.attributes = _.extend({
            days: 1,
            hours: 0,
            minutes: 0,
            seconds: 3
        }, this.model.attributes);
        this.render();
        this.listenTo(this.model, "change", this.update);
        var self = this;
        $(window.setInterval(function(){
            self.model.set("seconds", self.model.get("seconds") - 1);
        }, 1000));
    },

    update: function() {
        var atts = this.model.attributes;
        if(atts.seconds < 0) {
            this.model.set("minutes", this.model.get("minutes") - 1);
            this.model.set("seconds", 59);
        }
        if(atts.minutes < 0) {
            this.model.set("hours", this.model.get("hours") - 1);
            this.model.set("minutes", 59);
        }
        if(atts.hours < 0) {
            this.model.set("days", this.model.get("days") - 1);
            this.model.set("hours", 23);
        }
        this.render();
    }
});

$(function() {
    window.clock_view = new ClockView({el: $("#clock-view-el")});
});