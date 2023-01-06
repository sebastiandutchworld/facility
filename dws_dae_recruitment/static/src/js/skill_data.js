odoo.define('dws_dae_recruitment.skill_data', function (require) {
    "use strict";
    
    var publicWidget = require('web.public.widget');
    
    publicWidget.registry.skillTypeOptions = publicWidget.Widget.extend({
        selector: '.modal_new_skill_line, .model_edit_skill_line',
        events: {
            'change select[name="skill_type_id"]': '_onskillTypeChange',
        },
        start: function () {
            var def = this._super.apply(this, arguments);

            this.$skill = this.$('select[name="skill_id"]');
            this.$skillOptions = this.$skill.filter(':enabled').find('option:not(:first)');
            this._adaptSkillForm();
            
            this.$skilllevel = this.$('select[name="skill_level_ids"]');
            this.$skilllevelOptions = this.$skilllevel.filter(':enabled').find('option:not(:first)');
            this._adaptSkillLevelForm();

            return def;
        },
        _adaptSkillForm: function () {

            var $skilltype = this.$('select[name="skill_type_id"]');
            var skilltypeID = ($skilltype.val() || 0);
            this.$skillOptions.detach();
            var $displayedSkill = this.$skillOptions.filter('[data-skilltype_id=' + skilltypeID + ']');
            var nb = $displayedSkill.appendTo(this.$skill).show().length;
            this.$skill.parent().toggle(nb >= 1);
        },
        
        _adaptSkillLevelForm: function () {
            var $skilltype = this.$('select[name="skill_type_id"]');
            var skilltypeID = ($skilltype.val() || 0);
            this.$skilllevelOptions.detach();
            var $displayedSkilllevel = this.$skilllevelOptions.filter('[data-skill_id=' + skilltypeID + ']');
            var nb = $displayedSkilllevel.appendTo(this.$skilllevel).show().length;
            this.$skilllevel.parent().toggle(nb >= 1);
        },
        _onskillTypeChange: function () {
            this._adaptSkillForm();
            this._adaptSkillLevelForm();
        },
    });
});