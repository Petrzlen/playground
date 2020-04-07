import operator as op
import math

def ncr(n, r):
    r = min(r, n-r)
    numer = reduce(op.mul, xrange(n, n-r, -1), 1)
    denom = reduce(op.mul, xrange(1, r+1), 1)
    return numer//denom

interviews = 5
pass_rate = 0.58  # 22 pass, 16 rejects, 22/38

# if your pass rate is `prob`, and candidates are randomly distributed,
# what is the likelihood you will say `yeses` number of yeses.
for yeses in range(interviews + 1):
  b = math.pow(pass_rate, yeses) * math.pow((1 - pass_rate), (interviews - yeses))
  print '%d: %.2f' % (yeses, ncr(interviews, yeses) * b)

