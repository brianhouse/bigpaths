#!/usr/bin/env python3

import yaml, json, datetime, jinja2

fields = ['time', 'address', 'place', 'action', 'observation', 'images', 'transition']
transition_fields = ['time', 'mode', 'images']

images = []

def render(template_name, template_values=None, **kwargs):
    if type(template_values) == dict:
        template_values.update(kwargs)
    else:
        template_values = kwargs
    renderer = jinja2.Environment(loader=jinja2.FileSystemLoader("."))
    output = renderer.get_template(template_name).render(template_values)
    return output        

def adjust(text):
    text = text.replace(" -- ", "&mdash;&mdash;")
    text = text.replace("'", "&rsquo;")
    text = text.replace(".JPG", ".jpg")
    text = text.replace(".TIF", ".jpg")
    text = text.replace(".dng", ".jpg")
    return text

def parse(days):
    output = []
    previous_time = None
    for day in days:
        entries = days[day]
        for entry in entries:
            error = False
            for field in fields:
                if field not in entry or entry[field] is None or not len(str(entry[field]).strip()):
                    error = field
                    break
            try:
                if entry['time'] == "WAKE":
                    if previous_time.hour < 8:
                        entry['time'] = previous_time.strftime("%A")
                    else:
                        entry['time'] = (previous_time + datetime.timedelta(days=1)).strftime("%A")
                    entry['address'] = 'SKIP'
                else:
                    previous_time = entry['time']
                    entry['time'] = entry['time'].strftime("%A, %I:%M%p").replace(" 0", " ").replace("AM", "am").replace("PM", "pm")                    
            except Exception as e:
                error = e
            if not error:
                if entry['transition'] != "SLEEP":
                    for field in transition_fields:
                        if field not in entry['transition'] or entry['transition'][field] is None or not len(str(entry['transition'][field]).strip()):
                            error = "transition " + field
                            break
                    try:
                        entry['transition']['time'] = entry['transition']['time'].strftime("%I:%M%p").lstrip("0").replace("AM", "am").replace("PM", "pm")
                    except Exception as e:
                        error = e                
            if error:
                print(json.dumps(entry, indent=4, default=lambda x: str(x)))
                print("Missing %s" % error)
                return output
            print(json.dumps(entry, indent=4))
            print("GOOD")
            for image in entry['images']:
                images.append(image)
            if 'images' in entry['transition']:
                for image in entry['transition']['images']:
                    images.append(image)
            output.append(json.loads(adjust(json.dumps(entry))))
    return output, images


with open("master_narrative.yaml") as f:
    try:        
        days = yaml.load(f)
    except yaml.parser.ParserError as e:
        print(e)
        exit()
output, images = parse(days)

result = render("template.html", entries=output)
with open("index.html", 'w') as f:
    f.write(result)

with open("used_images.txt", 'w') as f:
    for image in images:
        if image is not None:
            f.write(adjust(image) + "\n")