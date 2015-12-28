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

var DescriptionView = Backbone.View.extend({
    initialize: function(options){
        _.bindAll(this, "render");
        this.model = options.model || new Backbone.Model();
        this.listenTo(this.model, "change", this.render);
        this.render()
    },

    render: function() {
        this.$(".brief-desc").text(this.model.get("description"));
    }
});

var FindOutMoreView = Backbone.View.extend({
    events: {
        "click .find-more-a": "toggle"
    },

    initialize: function (options) {
        _.bindAll(this, "render", "toggle");
        this.model = options.model || new Backbone.Model({more_info: "None available at the moment."});
        this.toggled = false;
        this.listenTo(this.model, "change:more_info", this.render);
    },

    toggle: function() {
        this.toggled = !this.toggled;
        this.render();
    },

    render: function() {
        if( this.toggled ) {
            this.$(".find-more-a").text("Click here to close this description.");
            this.$(".find-out-more").html(this.model.get("more_info"));
        } else {
            this.$(".find-more-a").text("Click here to find out more.");
            this.$(".find-out-more").html("");
        }
    }
});

var ContainerView = Backbone.View.extend({
    events: {
        "click .dropdown-item": "change_catastrophe_model"
    },

    initialize: function() {
        _.bindAll(this, "update_subviews", "render_chooser", "change_catastrophe_model");
        this.catastrophe_collection = new CatastropheCollection();
        this.clock_view = new ClockView({el: this.$("#clock-view-el")});
        this.desc_view = new DescriptionView({el: this.$("#desc-el")});
        this.find_out_more_view = new FindOutMoreView({el: this.$("#more-info-el")});
        this.fetch_catastrophe_collection();
    },

    update_subviews: function() {
        var catastrophe_model = this.catastrophe_model;
        this.clock_view.catastrophe_model.set(catastrophe_model.attributes);
        this.desc_view.model.set({description: catastrophe_model.get("description")});
        this.find_out_more_view.model.set({more_info: catastrophe_model.get("more_info")});
        this.render_chooser();
    },

    render_chooser: function() {
        var dropdown_menu = this.$("#chooser-el .dropdown-menu");
        dropdown_menu.html("");
        this.catastrophe_collection.forEach(function(catastrophe){
            var li = $("<li></li>").addClass("dropdown-item");
            var a = $("<a href='#'>").attr("data-id", catastrophe.cid).text(catastrophe.get("name"));
            li.append(a);
            dropdown_menu.append(li);
        });
    },

    change_catastrophe_model: function(ev) {
        var el = $(ev.target);
        this.catastrophe_model = this.catastrophe_collection.get(el.attr("data-id"));
        this.update_subviews();
    },

    fetch_catastrophe_collection: function() {
        var self = this;
        this.catastrophe_collection.fetch({
            success: function() {
                self.catastrophe_model = self.catastrophe_collection.findWhere({name: "California dries up"});
                self.update_subviews();
            },
            error: function() {
                console.log("Couldn't retrieve...");
            }
        });
    }
});

$(function() {
    window.clock_viev = new ContainerView({el: "#container-el"});
});

if (!String.prototype.repeat) {
    String.prototype.repeat = function(count) {
        'use strict';
        if (this == null) {
            throw new TypeError('can\'t convert ' + this + ' to object');
        }
        var str = '' + this;
        count = +count;
        if (count != count) {
            count = 0;
        }
        if (count < 0) {
            throw new RangeError('repeat count must be non-negative');
        }
        if (count == Infinity) {
            throw new RangeError('repeat count must be less than infinity');
        }
        count = Math.floor(count);
        if (str.length == 0 || count == 0) {
            return '';
        }
        // Ensuring count is a 31-bit integer allows us to heavily optimize the
        // main part. But anyway, most current (August 2014) browsers can't handle
        // strings 1 << 28 chars or longer, so:
        if (str.length * count >= 1 << 28) {
            throw new RangeError('repeat count must not overflow maximum string size');
        }
        var rpt = '';
        for (;;) {
            if ((count & 1) == 1) {
                rpt += str;
            }
            count >>>= 1;
            if (count == 0) {
                break;
            }
            str += str;
        }
        return rpt;
    }
}