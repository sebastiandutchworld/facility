import re
import logging
from lxml import etree, html

from odoo import api, models

_logger = logging.getLogger(__name__)

class MailRenderMixin(models.AbstractModel):
    _inherit = "mail.render.mixin"

    def remove_href_odoo(self, value, remove_parent=True, remove_before=False):
        if len(value) < 20:
            return value
        # has_odoo_link = re.search(r"<a\s(.*)odoo\.com", value, flags=re.IGNORECASE)
        # python says that type(value) is 'str', but re.search doesn't like that 'str' type, so we convert str to... str
        has_odoo_link = re.search(r"<a\s(.*)odoo\.com", str(value), flags=re.IGNORECASE)
        if has_odoo_link:
            tree = etree.HTML(
                value
            )  # html with brlken links   tree = etree.fromstring(value) just xml

            disable_buttons = self.env["ir.config_parameter"].sudo().get_param(
                "dws_mail_debrand.disable_buttons")

            if disable_buttons:
                odoo_achors = tree.xpath('//a[contains(@href,"odoo.com") or contains(@style,"border-radius: 5px;")]')
            else:
                odoo_achors = tree.xpath('//a[contains(@href,"odoo.com")]')
            
            for elem in odoo_achors:
                parent = elem.getparent()
                previous = elem.getprevious()

                if remove_before and not remove_parent and previous:
                    # remove 'using' that is before <a and after </span>
                    bytes_text = etree.tostring(
                        previous, pretty_print=True, method="html"
                    )
                    only_what_is_in_tags = bytes_text[: bytes_text.rfind(b">") + 1]
                    data_formatted = html.fromstring(only_what_is_in_tags)
                    parent.replace(previous, data_formatted)
                if parent.getparent() and remove_parent:
                    # anchor <a href odoo has a parent powered by that must be removed
                    parent.getparent().remove(parent)
                else:
                    if parent.tag == "td":  # also here can be powered by
                        parent.getparent().remove(parent)
                    else:
                        parent.remove(elem)
            value = etree.tostring(tree, pretty_print=True, method="html")
        if type(value) is str:
            value = re.sub("[^(<)(</)]odoo", "", value, flags=re.IGNORECASE)
        elif type(value) is bytes:
            value = re.sub(b"[^(<)(</)]odoo", b"", value, flags=re.IGNORECASE)

        return value

    @api.model
    def _render_template(
        self,
        template_src,
        model,
        res_ids,
        engine="qweb",
        add_context=None,
        options=None,
        post_process=False,
    ):
        """replace anything that is with odoo in templates
        if is a <a that contains odoo will delete it completly
        original:
         Render the given string on records designed by model / res_ids using
        the given rendering engine. Currently only jinja is supported.

        :param str template_src: template text to render (jinja) or  (qweb)
          this could be cleaned but hey, we are in a rush
        :param str model: model name of records on which we want to perform rendering
        :param list res_ids: list of ids of records (all belonging to same model)
        :param string engine: jinja
        :param post_process: perform rendered str / html post processing (see
          ``_render_template_postprocess``)

        :return dict: {res_id: string of rendered template based on record}"""

        orginal_rendered = super()._render_template(
            template_src,
            model,
            res_ids)#,
        #     engine="qweb", #alternatives tried, qweb, inline_template
        #     options=None,
        #     add_context=None,
        #     post_process=False,
        # )

        for key in res_ids:
            orginal_rendered[key] = self.remove_href_odoo(orginal_rendered[key])

        return orginal_rendered


class MailMail(models.AbstractModel):
    _inherit = "mail.mail"

    # in messages from objects is adding using Odoo that we are going to remove

    @api.model_create_multi
    def create(self, values_list):
        for index, _value in enumerate(values_list):
            values_list[index]["body_html"] = self.env[
                "mail.render.mixin"
            ].remove_href_odoo(
                values_list[index]["body_html"], remove_parent=1, remove_before=1
            )

        return super().create(values_list)
