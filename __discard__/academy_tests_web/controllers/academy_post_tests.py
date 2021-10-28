# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################
#pylint: disable=I0011,R0201,R0903,C0103,W0611,F0401,W0613,W0612,W0703

from openerp.http import route, request, Controller
from openerp.tools.translate import _
from logging import getLogger
from openerp.addons.web.controllers.main import serialize_exception, content_disposition

import json
import base64

_logger = getLogger(__name__)


class PostTests(Controller):
    """ Allow teachers to publish tests through Odoo website

        Routes:
          /posted-tests: allow students to access tests through the Odoo web
          /posted-test: allow to view a single test
    """

    @route('/academy/publish/tests', type='http', auth='user', website=True)
    def posted_tests(self, **kw):
        """ Allow students to access tests through the Odoo web
        """

        academy_tests_domain = [('id', '>=', 1)]
        academy_tests_obj = request.env['academy.tests.test']
        academy_tests_set = academy_tests_obj.search(academy_tests_domain)

        result = request.render('academy_tests_web.academy_post_tests', {
            'tests': academy_tests_set,
        })

        return result


    @route('/academy/publish/test', type='http', auth='user', website=True)
    def posted_test(self, **kw):
        """ Allow students to view a single test
        """

        academy_tests_domain = [('id', '=', kw['test_id'])]
        academy_tests_obj = request.env['academy.tests.test']
        academy_tests_set = academy_tests_obj.search(academy_tests_domain)

        result = request.render('academy_tests_web.academy_post_test_test', {
            'test_id': academy_tests_set,
            'edit': self._has_edit_rights(request.env.context['uid'])
        })

        return result


    @route('/ajax/proccess-impugnment', type='http', auth='user')
    def proccess_impugnment(self, **kw):
        """ Proccess Ajax request """

        try:
            inpugnment_obj = request.env['academy.tests.question.impugnment']

            values = {
                'name' : kw['name'],
                'description' : kw['description'],
                'question_id' : kw['question_id']
            }

            inpugnment_new = None

            try:
                inpugnment_new = inpugnment_obj.create(values)
            except Exception as ex:
                pass

            assert inpugnment_new, u'Inpugnment could not be stored in database'

            result = request.render('academy_tests_web.academy_post_test_impugnment_response', {
                'inpugnment': kw,
            })

            result = result
        except Exception as ex:
            print('Error', ex)
            result = ex

        return result


    @route('/ajax/get-question', csrf=True, type='json', auth='user')
    def get_question(self, **kw):
        """ Proccess Ajax request to get question
            :return: 400 (Bad Request), 204 (No Content), 200 (Success)
        """

        result, html = 400, None

        if kw and isinstance(kw, dict) and 'question_id' in kw:

            result = 204

            question_id = int(kw['question_id'])
            academy_tests_question_obj = request.env['academy.tests.question']
            academy_tests_question_set = academy_tests_question_obj.browse(question_id)

            if academy_tests_question_set:
                mode = kw.get('mode', 'show')

                if mode == 'edit':
                    if self._has_edit_rights(request.env.context['uid']):
                        result = 200
                        view = request.env['ir.model.data'].get_object(
                            'academy_tests_web', 'academy_post_test_question_edit')
                        html = view.render(
                            {'question_id': academy_tests_question_set}, engine='ir.qweb')

                        html = html.decode('utf-8', errors='replace')
                    else:
                        result = 401
                else:
                    result = 200
                    view = request.env['ir.model.data'].get_object(
                        'academy_tests_web', 'academy_post_test_question_show')

                    html = view.render(
                        {'question_id': academy_tests_question_set}, engine='ir.qweb')

                    html = html.decode('utf-8', errors='replace')

        return json.dumps({'result': result, 'html': str(html)})


    @route('/ajax/update-question', csrf=False, type='json', auth="public")
    def update_question(self, **kw):
        """ Proccess Ajax request to update question"""

        question_id = int(kw.pop('question_id'))
        academy_tests_question_obj = request.env['academy.tests.question']
        academy_tests_question_set = academy_tests_question_obj.browse(question_id)

        academy_tests_question_set.write(kw)

        academy_tests_question_set = academy_tests_question_obj.browse(question_id)

        return json.dumps(academy_tests_question_set.read())


    @route('/academy/publish/answers', type='http', auth='user', website=True)
    def answers_table(self, **kw):
        """ Return the answers table for test
        """

        academy_tests_domain = [('id', '=', kw['test_id'])]
        academy_tests_obj = request.env['academy.tests.test']
        academy_tests_set = academy_tests_obj.search(academy_tests_domain)

        academy_tests_answers_domain = [('test_id', '=', int(kw['test_id']))]
        academy_tests_answers_obj = request.env['academy.tests.answers.table']
        academy_tests_answers_set = academy_tests_answers_obj.search(academy_tests_answers_domain)

        result = request.render('academy_tests_web.academy_tests_answers_table', {
            'test': academy_tests_set,
            'answers': academy_tests_answers_set
        })

        return result


    # Following lines should be removed
    ###########################################################################
    # @route('/web/binary/download_document', type='http', auth="public")
    # @serialize_exception
    # def download_document(self, **kw):
    #     """ Download link for files stored as binary fields.
    #     :param str model: name of the model to fetch the binary from
    #     :param str field: binary field
    #     :param str id: id of the record from which to fetch the binary
    #     :param str filename: field holding the file's name, if any
    #     :returns: :class:`werkzeug.wrappers.Response`
    #     """


    #     ir_attachment_domain = [('id', '=', int(kw['id']))]
    #     ir_attachment_obj = request.env['ir.attachment']
    #     ir_attachment_set = ir_attachment_obj.search(ir_attachment_domain)

    #     filename = ir_attachment_set.datas_fname
    #     filecontent = base64.b64decode(ir_attachment_set.datas or '')
    #     if not filecontent:
    #         return request.not_found()
    #     else:
    #         return request.make_response(filecontent, \
    #             [('Content-Type', ir_attachment_set.mimetype), \
    #             ('Content-Disposition', content_disposition(filename))])

    # -------------------------- AUXILIAR METHODS -----------------------------

    @staticmethod
    def _has_edit_rights(uid):
        """ Get current user
        """

        # user_obj = request.env['res.users']
        # user_set = user_obj.browse(uid)

        # return user_set.user_has_groups('academy_base.res_users_demo_teacher')

        return True

