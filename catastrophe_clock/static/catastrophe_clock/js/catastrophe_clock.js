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
        _.bindAll(this, "render", "template", "update", "convert");
        this.model = options.model || new Backbone.Model();
        this.catastrophe_model = options.catastrophe_model || new Backbone.Model();
        this.model.attributes = _.extend({
            days: 0,
            hours: 6,
            minutes: 6,
            seconds: 6
        }, this.model.attributes);
        this.render();
        var self = this;
        $(window.setInterval(function(){
            self.model.set("seconds", self.model.get("seconds") - 1);
        }, 1000));
        this.listenTo(this.model, "change", this.update);
        this.listenTo(this.catastrophe_model, "change", this.convert)
    },

    convert: function() {
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

var DescriptionView = Backbone.View.extend({});

var ContainerView = Backbone.View.extend({
    initialize: function() {
        _.bindAll(this, "update_subviews");
        this.catastrophe_collection = new CatastropheCollection();
        this.clock_view = new ClockView({el: this.$("#clock-view-el")});
        this.fetch_catastrophe_collection();
    },

    update_subviews: function() {
        var catastrophe_model = this.catastrophe_collection.findWhere({name: "Miami sinks"});
        this.clock_view.catastrophe_model.set(catastrophe_model.attributes);
    },

    fetch_catastrophe_collection: function() {
        var self = this;
        this.catastrophe_collection.fetch({
            success: self.update_subviews,
            error: function() {
                console.log("Couldn't retrieve...");
            }
        });
    }
});

$(function() {
    window.clock_viev = new ContainerView({el: "#container-el"});
});