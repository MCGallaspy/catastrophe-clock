var CatastropheCollection = Backbone.Collection.extend({
    url: '/api/catastrophes/',
    parse: function(response) {
        return response.results;
    }
});


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
        _.bindAll(this, "render", "template", "update", "convert", "fetch_and_convert");
        this.model = options.model || new Backbone.Model();
        this.model.attributes = _.extend({
            days: 0,
            hours: 6,
            minutes: 6,
            seconds: 6
        }, this.model.attributes);
        this.render();
        this.listenTo(this.model, "change", this.update);
        var self = this;
        $(window.setInterval(function(){
            self.model.set("seconds", self.model.get("seconds") - 1);
        }, 1000));
        this.fetch_and_convert();
    },

    fetch_and_convert: function() {
        this.collection = this.collection || new CatastropheCollection();
        this.collection.fetch({
            success: this.convert,
            error: function() {
                console.log("Couldn't retrieve...");
            }
        });
    },

    convert: function() {
        this.catastrophe_model = this.collection.at(0);
        var arrival = new Date(this.catastrophe_model.get("arrival_date"));
        var now = Date.now();
        var diff = arrival - now; // In milliseconds
        var diff_secs = Math.floor(diff / 1000);
        this.model.set({
            seconds: diff_secs % 60,
            minutes: Math.floor(diff_secs / 60) % 60 ,
            hours: Math.floor(diff_secs / (60 * 60)) % 24,
            days: Math.floor(diff_secs / (60 * 60 * 24))
        });
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