
# generate outputs
def generate():
    day = []
    index = random.choice(range(len(X)))
    x = X[index]
    for i in range(PERIODS):
        distribution = model.predict(np.array([x[-MEMORY:]]), verbose=0, batch_size=1)[0]
        y = sample(distribution, config['temperature'])
        x = np.append(x, to_categorical(y, CATEGORIES), axis=0)
        day.append(y)
    log.debug(day)
    return day

def sample(distribution, temperature): # thx gene
    a = np.log(distribution) / temperature
    p = np.exp(a) / np.sum(np.exp(a))
    choices = range(len(distribution))
    return np.random.choice(choices, p=p)

if not config['autonomous']:
    k = input("Generate how many examples? [10]: ")
    n = int(k.lower()) if len(k) else 10
else:
    n = 100
log.info("Generating %d examples..." % n)
days = []
for i in range(n):    
    day = generate()
    days.append(day)
util.save("data/%s_%s_output.pkl" % (MODEL, config['temperature']), days)
log.info("--> done")
