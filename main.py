import json
import re
from copy import deepcopy


class Grammer:
    def __init__(self):
        self.nonterms = set()
        self.terms = set()
        self.start_nonterm = None
        self.productions = {}

    @staticmethod
    def from_json(file_path):
        grammer = Grammer()

        file = open(file_path)
        doc = json.load(file)
        
        grammer.nonterms = set(doc['nonterms'])
        grammer.terms = set(doc['terms'])
        grammer.productions = doc['productions']
        grammer.start_nonterm = doc['start_nonterm']

        return grammer
    
    @staticmethod
    def remove_left_recursion_for(nonterm, productions):
        transit_nonterm = f'{nonterm}\''
        transit_nonterm_productions = []

        new_productions = []
        for production in productions:
            if production == 'ε':
                transit_nonterm_productions.append('ε')
                new_productions.append(transit_nonterm)
                continue

            match = re.match(f'{nonterm}(.*)', production)
            if match is not None:
                transit_nonterm_productions.append(f'{match.group(1)}{transit_nonterm}')
                continue

            new_productions.append(f'{production}{transit_nonterm}')

        return nonterm, new_productions, transit_nonterm, transit_nonterm_productions

    def closure(self, nonterm, prev_nonterm):
        productions_closure = []
        for production in self.productions[nonterm]:
            match = re.match(f'{prev_nonterm}(.*)', production)
            if match is not None:
                for prev_nonterm_production in self.productions[prev_nonterm]:
                    productions_closure.append(f'{prev_nonterm_production}{match.group(1)}')
                continue
            
            productions_closure.append(production)

        return productions_closure

    def removed_left_recursion(self):
        grammer = Grammer()
        grammer.terms = deepcopy(self.terms)
        grammer.start_nonterm = self.start_nonterm

        for _, nonterm in enumerate(reversed(sorted(self.nonterms))):
            grammer.nonterms.add(nonterm)
            grammer.productions[nonterm] = self.productions[nonterm]

            for _, prev_nonterm in enumerate(reversed(sorted(self.nonterms))):
                if  nonterm == prev_nonterm:
                    break

                _, new_productions, transit_nonterm, transit_nonterm_productions = self.remove_left_recursion_for(
                    nonterm, self.closure(nonterm, prev_nonterm)
                )
                
                if len(transit_nonterm_productions) == 0:
                    continue

                grammer.nonterms.add(transit_nonterm)
                grammer.productions.update({nonterm: new_productions})
                grammer.productions.update({transit_nonterm: transit_nonterm_productions})

        return grammer   

    @staticmethod
    def common_prefix(strings):
        return ''.join([x[0] for x in zip(*strings) if x == (x[0], ) * len(x)])

    def left_factorization(self):
        grammer = Grammer()
        grammer.terms = deepcopy(self.terms)
        grammer.start_nonterm = self.start_nonterm

        for nonterm in self.nonterms:
            grammer.nonterms.add(nonterm)
            if len(self.productions[nonterm]) < 2:
                grammer.productions[nonterm] = deepcopy(self.productions[nonterm])
                continue

            productions = sorted(self.productions[nonterm])
            
            f = 0
            t = 1
            k = 1
            while t < len(productions):
                prefix = self.common_prefix(productions[f:t + 1])
                t += 1

                if prefix == '':
                    grammer.productions.setdefault(nonterm, []).append(productions[f])
                    f += 1
                    continue

                while t < len(productions):
                    new_prefix = self.common_prefix(productions[f:t + 1])

                    if prefix != new_prefix:
                        new_nonterm = f'{nonterm}{k}'
                        k += 1

                        grammer.nonterms.add(new_nonterm)
                        grammer.productions.setdefault(nonterm, []).append(f'{prefix}{new_nonterm}')
                        for p in range(f, t):
                            grammer.productions.setdefault(new_nonterm, []).append(productions[p][len(prefix):])

                        f = t
                        t += 1
                        break

                    t += 1

            if t - f == 1:
                grammer.productions.setdefault(nonterm, []).append(productions[-1])
            else:
                new_nonterm = f'{nonterm}{k}'

                grammer.nonterms.add(new_nonterm)
                grammer.productions.setdefault(nonterm, []).append(f'{prefix}{new_nonterm}')
                for p in range(f, t):
                    grammer.productions.setdefault(new_nonterm, []).append(productions[p][len(prefix):])

        return grammer

    def removed_unreachables(self):
        grammer = Grammer()
        grammer.start_nonterm = self.start_nonterm

        v = [set(self.start_nonterm)]

        while True:
            v.append(set(v[-1]))
            
            for symbol in self.nonterms | self.terms:
                for key in self.productions:
                    if key not in v[-2]:
                        continue
                    
                    for rhs in self.productions[key]:
                        if re.search(f'.*{re.escape(symbol)}.*', rhs):
                            v[-1].add(symbol)

            if v[-1] == v[-2]:
                break
        
        grammer.nonterms = self.nonterms & v[-1]
        grammer.terms = self.terms & v[-1]
        
        productions = {}
        for key in self.productions:
            if key in grammer.nonterms:
                productions[key] = self.productions[key]
        grammer.productions = productions

        return grammer

    def __str__(self):
        return \
            f'{{\n'\
            f'    {{{', '.join(sorted(self.nonterms))}}},\n'\
            f'    {{{', '.join(sorted(self.terms))}}},\n'\
            f'    {{\n        {',\n        '.join([f'{k} -> {' | '.join(self.productions[k])}' for k in sorted(self.productions.keys())])}\n    }},\n'\
            f'    {self.start_nonterm}\n'\
            f'}}'

def main():
    file_path = 'grammer.json'
    # file_path = input()

    grammer = Grammer.from_json(file_path)
    print(f'input\n{grammer}', end='\n\n')
    grammer = grammer.removed_left_recursion()
    print(f'removed recursion\n{grammer}', end='\n\n')
    grammer = grammer.left_factorization()
    print(f'factorization\n{grammer}', end='\n\n')
    grammer = grammer.removed_unreachables()
    print(f'removed unreachables\n{grammer}')

if __name__ == '__main__':
    main()