function accessesSchema(config) {
  return {
    'title': 'Доступы в amoCRM',
    'type': 'object',
    'properties' : {
      'user' : {
        'type' : 'string',
          'minLength': 4,
          'propertyOrder': 1,
          'description': 'Пользователь amoCRM'
      },
      'subdomain' : {
        'type' : 'string',
          'minLength': 4,
          'propertyOrder': 2,
          'description': 'Субдомен в amoCRM'
      },
      'hash' : {
        'type' : 'string',
        'minLength': 4,
        'propertyOrder': 3,
        'description': 'Hash указанного пользователя'
      },
    }
  };
}

function formSchema(config){
  return {
    'title': 'Правила обработки',
    'type': 'object',
    'properties' : {
      'responsible_user' : {
        'title': 'Ответственный за сделки',
        'type' : 'string',
        'enum': config['allowed_users'],
        'propertyOrder': 4,
        'description': 'Если указан, то сделки будут расрпделеться ТОЛЬКО на него'
      },
      'department' : {
        'title': 'Отдел, обрабатывающий сделки',
        'type' : 'string',
        'propertyOrder': 5,
        'description': 'Если \'Не выбрано\', то распределение идет вне зависимости от отдела',
        'enum': config['allowed_departments']
      },
      'status_for_new' : {
        'title': 'Статус для новых обращений',
        'type' : 'string',
        'propertyOrder': 6,
        'enum': config['allowed_statuses']
      },
      'status_for_rec' : {
        'title': 'Статус для повторных обращений',
        'type' : 'string',
        'propertyOrder': 7,
        'enum': config['allowed_statuses']
      },
      'generate_tasks_for_rec' : {
        'title': 'Создавать задачи при обращении человека с существующей \
          сделкой или покупателем',
        'propertyOrder': 8,
        'type' : 'checkbox'
      },
      'rec_lead_task_text' : {
        'title': 'Текст для этой задачи',
        'propertyOrder': 8,
        'type' : 'string'
      },
      'time_to_complete_rec_task' : {
        'title': 'Время на выполнение этой задачи (минуты)',
        'propertyOrder': 9,
        'type' : 'integer'
      },
      'tag_for_rec' : {
        'title': 'Тег для повторных обращений',
        'propertyOrder': 10,
        'type' : 'string'
      },

      'another_distribution': {
        'title': 'Использовать правила распределения из другой формы',
        'type': 'string',
        'propertyOrder': 11,
        'enum': config['forms'],
        'description': 'При включении, ВСЕ правила из этой формы игнорируются! \
          (распределение для форм будет общим)'
      },

      'distribution_settings' : {
        'type': 'array',
        'options': {
          'collapsed': true,
          'disable_array_reorder' : true,
        },
        'format': 'table',
        'propertyOrder': 12,
        'description': 'Внимание! Изменяя это поле, вы сбросите счетчик лидов!<br> \
        В распределении будут участвовать только люди из выбранного отдела (если выбран)<br>\
        (Если оставить пустым, применяться не будет)',
        'title': 'Список людей, на которых распределяются сделки',
        'uniqueItems': true,
        'items': {
          'type': 'object',
          'title': 'Пользователь',
          'uniqueItems': true,
          'properties': {
            'user': {
              'title': 'Менеджер',
              'type': 'string',
              'enum': config['allowed_users'].slice(0, -1)
            },
            'weight': {
              'title': 'Вес',
              'type': 'integer'
            },
            'allowed_time' : {
              'title': 'Рабочее время',
              'type': 'array',
              'options': {
                'collapsed': false,
                'disable_array_reorder' : true,
              },
              'format': 'table',
              'uniqueItems': true,
              'items': {
                'type': 'object',
                'uniqueItems': true,
                'properties': {
                  'week_day': {
                    'type': 'string',
                    'title': 'День недели',
                    'enum': config['weekdays']
                  },
                  'from': {
                    'title': 'От',
                    'type': 'string',
                    'format': 'time'
                  },
                  'to': {
                    'title': 'До',
                    'type': 'string',
                    'format': 'time'
                  }
                }
              }
            }
          }
        }
      },

      // --------------------------------------------------
      'contact_fields_to_check_dups' : {
        'type': 'array',
        'options': {
          'collapsed': true
        },
        'format': 'table',
        'propertyOrder': 20,
        'title': 'Поля для проверки дублей контакта',
        'uniqueItems': true,
        'items': {
          'type': 'object',
          'title': 'Поле',
          'uniqueItems': true,
          'properties': {
            'field': {
              'type': 'string',
              'enum': config['allowed_fields']['contacts'].slice(0, -3)
            }
          }
        }
      },
      'contact_fields' : {
        'type': 'array',
        'options': {
          'collapsed': true
        },
        'format': 'table',
        'propertyOrder': 21,
        'title': 'Соответствие полей контакта',
        'uniqueItems': true,
        'items': {
          'type': 'object',
          'title': 'Поле',
          'properties': {
            'amoCRM': {
              'type': 'string',
              'enum': config['allowed_fields']['contacts'],
            },
            'site': {
              'type': 'string',
              'minLength': 3
            }
          }
        }
      },
      // ---------------------------------------------------------

      'company_fields_to_check_dups' : {
        'type': 'array',
        'options': {
          'collapsed': true
        },
        'format': 'table',
        'propertyOrder': 22,
        'title': 'Поля для проверки дублей компании',
        'uniqueItems': true,
        'items': {
          'type': 'object',
          'title': 'Поле',
          'uniqueItems': true,
          'properties': {
            'field': {
              'type': 'string',
              'enum': config['allowed_fields']['companies'].slice(0, -3)
            }
          }
        }
      },
      'company_fields' : {
        'type': 'array',
        'options': {
          'collapsed': true
        },
        'format': 'table',
        'propertyOrder': 23,
        'title': 'Соответствие полей компании',
        'uniqueItems': true,
        'items': {
          'type': 'object',
          'title': 'Поле',
          'properties': {
            'amoCRM': {
              'type': 'string',
              'enum': config['allowed_fields']['companies'],
            },
            'site': {
              'type': 'string',
              'minLength': 3
            }
          }
        }
      },
      // ----------------------------------------------------------

      'lead_fields' : {
        'type': 'array',
        'options': {
          'collapsed': true
        },
        'format': 'table',
        'propertyOrder': 24,
        'title': 'Соответствие полей сделки',
        'uniqueItems': true,
        'items': {
          'type': 'object',
          'title': 'Поле',
          'properties': {
            'amoCRM': {
              'type': 'string',
              'enum': config['allowed_fields']['leads'],
            },
            'site': {
              'type': 'string',
              'minLength': 3
            }
          }
        }
      },

      // ----------------------------------------------------------

      'exceptions' : {
        'type': 'array',
        'options': {
          'collapsed': true
        },
        'format': 'table',
        'propertyOrder': 64,
        'title': 'Исключения для формы',
        'uniqueItems': true,
        'items': {
          'type': 'object',
          'title': 'Исключение',
          'properties': {
            'exception': {
              'type': 'string',
            }
          }
        }
      }

    }
  };
}

$(document).ready(function(){

  function loadConfig(hash) {
    $.get('/getConfig', {'hash':hash, 'form_type':type}, function( data ) {
        var config = JSON.parse(data);
        if (!config['valid_amo']) {
          // alert('Неверные данные для входа в amoCRM!');
          $('.invalid-amo').show();
          if (hash != 'accesses') return;
        }

        $('.send').show();
        if (hash == 'accesses') var schema = accessesSchema(config);
        else {
          var schema = formSchema(config);

          // Set enum for schema
          if (config[type][hash]['allowed_enum']) {
            var typesArray = ['contact_fields', 'company_fields', 'lead_fields'];
            var arrayLength = typesArray.length;
            for (var i = 0; i < arrayLength; i++) {
              schema['properties'][typesArray[i]]['items']['properties']['site']['enum'] =
                config[type][hash]['allowed_enum'];
            }
          }

          handlerTypes = {
            'email' : 'emailHandler',
            'onpbx' : 'onpbxHandler',
            'site_forms' : 'siteHandler'
          }
          isPublic = {
            'email' : 'private_hash',
            'onpbx' : 'private_hash',
            'site_forms' : 'public_hash'
          }
          $('.form-path').text('https://'+document.domain+'/'+handlerTypes[type]+
            '?form='+hash+'&'+isPublic[type]+'='+config[isPublic[type]]);
          $('.form-path').show();
        }

        // Set default options
        JSONEditor.defaults.options.theme = 'bootstrap3';

        // Initialize the editor
        var editor = new JSONEditor(document.getElementById('editor_holder'),{
          schema: schema,
          required_by_default	: true
        });

        if (hash == 'accesses') {
          editor.setValue({
            'user' : config['user'],
            'hash' : config['hash'],
            'subdomain' : config['subdomain'],
          });
        } else {
          var contact_fields = new Array();
          for (var field in config[type][hash]['contact_data']) {
            contact_fields.push({
              'amoCRM' : field,
              'site' : config[type][hash]['contact_data'][field]
            });
          }
          var contact_fields_to_check_dups = new Array();
          for (var field in config[type][hash]['fields_to_check_dups']['contacts']) {
            contact_fields_to_check_dups.push({
              'field' : config[type][hash]['fields_to_check_dups']['contacts'][field],
            });
          }

          var company_fields = new Array();
          for (var field in config[type][hash]['company_data']) {
            company_fields.push({
              'amoCRM' : field,
              'site' : config[type][hash]['company_data'][field]
            });
          }
          var company_fields_to_check_dups = new Array();
          for (var field in config[type][hash]['fields_to_check_dups']['companies']) {
            company_fields_to_check_dups.push({
              'field' : config[type][hash]['fields_to_check_dups']['companies'][field],
            });
          }

          var lead_fields = new Array();
          for (var field in config[type][hash]['lead_data']) {
            lead_fields.push({
              'amoCRM' : field,
              'site' : config[type][hash]['lead_data'][field]
            });
          }

          editor.setValue({
            'responsible_user' : config['default_user'],
            'department' : config['default_department'],
            'status_for_new' : config['status_for_new'],
            'status_for_rec' : config['status_for_rec'],
            'generate_tasks_for_rec' : config[type][hash]['generate_tasks_for_rec'],
            'rec_lead_task_text' : config[type][hash]['rec_lead_task_text'],
            'time_to_complete_rec_task' : config[type][hash]['time_to_complete_rec_task']/60,
            'tag_for_rec' : config[type][hash]['tag_for_rec'],
            'another_distribution' : config['chosen_distr'],
            'distribution_settings' : config[type][hash]['distribution_settings'],

            'contact_fields': contact_fields,
            'contact_fields_to_check_dups' : contact_fields_to_check_dups,

            'company_fields' : company_fields,
            'company_fields_to_check_dups' : company_fields_to_check_dups,

            'lead_fields' : lead_fields,

            'exceptions' : config[type][hash]['exceptions']
          });
        }

        function getCookie(name) {
          var cookieValue = null;
          if (document.cookie && document.cookie != '') {
              var cookies = document.cookie.split(';');
              for (var i = 0; i < cookies.length; i++) {
                  var cookie = jQuery.trim(cookies[i]);
                  // Does this cookie string begin with the name we want?
                  if (cookie.substring(0, name.length + 1) == (name + '=')) {
                      cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                      break;
                  }
              }
          }
          return cookieValue;
        }

        $('.send').click(function(){
          var csrftoken = getCookie('csrftoken');
          $.ajaxSetup({
            beforeSend: function(xhr, settings) {
              xhr.setRequestHeader('X-CSRFToken', csrftoken);
            }
          });
          data = editor.getValue();
          data['form'] = hash;
          data['config_type'] = type;
          $.post('/setConfig', JSON.stringify(data), function() {
            location.reload();
          }, 'json');
        });

        if (hash != 'accesses') {
          $('.delete-form').show();
          $('.delete-form').click(function(){
            bootbox.confirm({
              message: "Вы дейстивтельно хотите удалить эту форму?",
              buttons: {
                  confirm: {
                      label: 'Да',
                      className: 'btn-success'
                  },
                  cancel: {
                      label: 'Нет',
                      className: 'btn-danger'
                  }
              },
              callback: function (result) {
                if (result) {
                  var csrftoken = getCookie('csrftoken');
                  $.ajaxSetup({
                    beforeSend: function(xhr, settings) {
                      xhr.setRequestHeader('X-CSRFToken', csrftoken);
                    }
                  });
                  data = {};
                  data['name'] = hash;
                  data['type'] = type;
                  $.post('/deleteForm', JSON.stringify(data), function() {
                    window.location.replace('/');
                  }, 'json');
                }
              }
            });


          });
        }
    });
  }

  var path = window.location.pathname;
  var arrVars = path.split("/");
  if (arrVars.length < 3) {
    var hash = arrVars[1];
    var type = 'no_type';
  } else {
    var type = arrVars[1];
    var hash = arrVars[2];
  }

  if (hash === '') hash = 'accesses';
  if (hash != 'add_form') loadConfig(hash);
});
