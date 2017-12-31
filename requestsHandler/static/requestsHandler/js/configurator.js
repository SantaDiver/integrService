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
    'title': 'Форма заявок с сайта',
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
        В распределении будут участвовать только люди из выбранного отдела (если выбран)',
        'title': 'Список людей, на которых распределяются сделки',
        'uniqueItems': true,
        'items': {
          'type': 'object',
          'title': 'Пользователь',
          'uniqueItems': true,
          'properties': {
            'user': {
              'type': 'string',
              'enum': config['allowed_users'].slice(0, -1)
            },
            'weight': {
              'type': 'integer'
            },
            'allowed_time' : {
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
                    'enum': config['weekdays']
                  },
                  'from': {
                    'type': 'string',
                    'format': 'time'
                  },
                  'to': {
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
      }
    }
  };
} 

$(document).ready(function(){

  function loadConfig(hash) {
    $.get('/getConfig', {'hash':hash}, function( data ) {
        var config = JSON.parse(data);
        if (!config['valid_amo']) {
          // alert('Неверные данные для входа в amoCRM!');
          $('.invalid-amo').show();
          if (hash != 'accesses') return;
        }

        if (hash == 'accesses') var schema = accessesSchema(config);
        else var schema = formSchema(config);
    
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
          for (var field in config[hash]['contact_data']) {
            contact_fields.push({
              'amoCRM' : field,
              'site' : config[hash]['contact_data'][field]
            });
          }
          var contact_fields_to_check_dups = new Array();
          for (var field in config[hash]['fields_to_check_dups']['contacts']) {
            contact_fields_to_check_dups.push({
              'field' : config[hash]['fields_to_check_dups']['contacts'][field],
            });
          }
          
          var company_fields = new Array();
          for (var field in config[hash]['company_data']) {
            company_fields.push({
              'amoCRM' : field,
              'site' : config[hash]['company_data'][field]
            });
          }
          var company_fields_to_check_dups = new Array();
          for (var field in config[hash]['fields_to_check_dups']['companies']) {
            company_fields_to_check_dups.push({
              'field' : config[hash]['fields_to_check_dups']['companies'][field],
            });
          }
          
          var lead_fields = new Array();
          for (var field in config[hash]['lead_data']) {
            lead_fields.push({
              'amoCRM' : field,
              'site' : config[hash]['lead_data'][field]
            });
          }
          
          editor.setValue({
            'responsible_user' : config['default_user'],
            'department' : config['default_department'],
            'status_for_new' : config['status_for_new'],
            'status_for_rec' : config['status_for_rec'],
            'generate_tasks_for_rec' : config[hash]['generate_tasks_for_rec'],
            'rec_lead_task_text' : config[hash]['rec_lead_task_text'],
            'time_to_complete_rec_task' : config[hash]['time_to_complete_rec_task']/60,
            'tag_for_rec' : config[hash]['tag_for_rec'],
            'another_distribution' : hash,
            'distribution_settings' : config[hash]['distribution_settings'],
            
            'contact_fields': contact_fields,
            'contact_fields_to_check_dups' : contact_fields_to_check_dups,
            
            'company_fields': company_fields,
            'company_fields_to_check_dups' : company_fields_to_check_dups,
            
            'lead_fields': lead_fields,
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
          $.post('/setConfig', JSON.stringify(data), function() {
            location.reload();
          }, 'json');
        });
        
        if (hash != 'accesses') {
          $('.delete').show();
          $('.delete').click(function(){
            var csrftoken = getCookie('csrftoken');
            $.ajaxSetup({
              beforeSend: function(xhr, settings) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
              }
            });
            data = {};
            data['name'] = hash;
            $.post('/deleteForm', JSON.stringify(data), function() {
              window.location.replace('/');
            }, 'json');
          });
        }
    });
  }

  var hash = window.location.pathname;
  hash = hash.substring(1);
  if (hash === '') hash = 'accesses';
  
  if (hash != 'add_form') loadConfig(hash);
  
});